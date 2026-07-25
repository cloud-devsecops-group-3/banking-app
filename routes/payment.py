# ============================================================
# routes/payment.py
# Handles the full payment flow.
#
# Real flow (matches the contract agreed with the ecommerce team):
#   1. POST /api/payment-requests   <- ecommerce calls this at checkout
#   2. GET  /qr/<transaction_id>.png -> ecommerce embeds this image
#   3. GET  /pay/<transaction_id>   -> customer opens this (scan or click);
#      redirects to /login first if not already logged in
#   4. POST /pay/<transaction_id>/confirm -> settle, then call the
#      ecommerce callback_url with the result
#   5. GET  /complete                -> success page, offers return_url
#
# Every step after (1) looks the transaction up by transaction_id and
# reads amount/merchant_account from the PaymentRequest row - never from
# a URL query string or a hidden form field. The paying account works the
# same way: it comes from session["account_id"] (set at login), never
# from a form field, so there's no account picker and nothing the
# browser sends can change which account gets debited.
# ============================================================

import uuid
from decimal import Decimal, InvalidOperation
from io import BytesIO

import qrcode
import requests
from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from database import db
from models import PaymentRequest
from utils.auth import login_required
from utils.helpers import get_account_by_id, process_payment

payment_bp = Blueprint("payment", __name__)


# ============================================================
# Real integration entry point - called by the ecommerce app
# ============================================================

@payment_bp.route("/api/payment-requests", methods=["POST"])
def create_payment_request():
    """
    What the ecommerce app calls at checkout.
    Body: {order_id, amount, merchant_account, callback_url, return_url?}
    Returns: {transaction_id, qr_url}
    """
    data = request.get_json(silent=True) or {}
    required = ("order_id", "amount", "merchant_account", "callback_url")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify(error=f"missing fields: {', '.join(missing)}"), 400

    try:
        amount = Decimal(str(data["amount"]))
        if amount <= 0:
            raise InvalidOperation
    except (TypeError, InvalidOperation):
        return jsonify(error="amount must be a positive number"), 400

    transaction_id = f"txn-{uuid.uuid4().hex[:16]}"
    payment_request = PaymentRequest(
        transaction_id=transaction_id,
        order_id=str(data["order_id"]),
        amount=amount,
        merchant_account=data["merchant_account"],
        callback_url=data["callback_url"],
        return_url=data.get("return_url"),
        status="PENDING",
    )
    db.session.add(payment_request)
    db.session.commit()

    base = current_app.config.get("BANKING_PUBLIC_BASE") or request.host_url.rstrip("/")
    qr_url = f"{base}/qr/{transaction_id}.png"
    return jsonify(transaction_id=transaction_id, qr_url=qr_url), 201


@payment_bp.route("/qr/<transaction_id>.png")
def qr_image(transaction_id):
    """Generated on demand - no file storage needed. The QR encodes a URL
    into this app's own /pay page, not raw payment details, so scanning
    it can't be used to forge a different amount."""
    pay_url = url_for("payment.pay_page", transaction_id=transaction_id, _external=True)
    img = qrcode.make(pay_url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


# ============================================================
# Customer-facing payment flow
# ============================================================

def _get_pending_payment_request(transaction_id):
    """Looks up a PaymentRequest by its public id. Returns None if it
    doesn't exist or has already been settled - callers should treat
    both cases as "nothing to pay here"."""
    pr = PaymentRequest.query.filter_by(transaction_id=transaction_id).first()
    if not pr or pr.status != "PENDING":
        return None
    return pr


@payment_bp.route("/pay/<transaction_id>", methods=["GET"])
@login_required
def pay_page(transaction_id):
    """The only page before settling. No account picker - the logged-in
    session already tells us which account is paying."""
    payment_request = _get_pending_payment_request(transaction_id)
    if not payment_request:
        return render_template("error.html", message="This payment link is invalid or already used."), 404

    account = get_account_by_id(session["account_id"])
    if not account:
        # Session points at an account that no longer exists - treat as
        # logged out rather than crash.
        session.clear()
        return redirect(url_for("auth.login", next=request.path))

    balance_after = Decimal(str(account.balance)) - Decimal(str(payment_request.amount))

    return render_template(
        "confirm_payment.html",
        account=account,
        transaction_id=transaction_id,
        order_id=payment_request.order_id,
        amount=payment_request.amount,
        merchant=payment_request.merchant_account,
        balance_after=balance_after,
    )


@payment_bp.route("/pay/<transaction_id>/confirm", methods=["POST"])
@login_required
def process(transaction_id):
    """Settles the payment, then calls the ecommerce app's webhook."""
    payment_request = _get_pending_payment_request(transaction_id)
    if not payment_request:
        return render_template("error.html", message="This payment link is invalid or already used."), 404

    # account_id comes ONLY from the session, never from a form field -
    # otherwise a user could edit a hidden input to pay from an account
    # that isn't theirs.
    account_id = session["account_id"]
    result = process_payment(account_id=account_id, payment_request=payment_request)

    if not result["success"]:
        account = get_account_by_id(account_id)
        balance_after = (
            Decimal(str(account.balance)) - Decimal(str(payment_request.amount)) if account else None
        )
        return render_template(
            "confirm_payment.html",
            account=account,
            transaction_id=transaction_id,
            order_id=payment_request.order_id,
            amount=payment_request.amount,
            merchant=payment_request.merchant_account,
            balance_after=balance_after,
            error=result["error"],
        )

    payment_request.status = "PAID"
    db.session.commit()

    _notify_ecommerce(payment_request, outcome="PAID")

    session["txn"] = {
        "reference": result["reference"],
        "order_id": payment_request.order_id,
        "amount": str(payment_request.amount),
        "merchant": payment_request.merchant_account,
        "return_url": payment_request.return_url,
    }
    return redirect(url_for("payment.complete"))


def _notify_ecommerce(payment_request, outcome):
    """Calls the ecommerce app's callback_url with the final status.
    Best-effort: if the ecommerce app is unreachable, the payment has
    still settled on our side - we don't roll back money that's already
    moved just because a notification failed. The ecommerce app's own
    order stays PENDING until it hears from us, which is the correct
    failure mode (visible and safe, not silently wrong)."""
    try:
        requests.post(
            payment_request.callback_url,
            json={
                "order_id": payment_request.order_id,
                "status": outcome,
                "transaction_id": payment_request.transaction_id,
            },
            # (connect_timeout, read_timeout) - a single float only bounds
            # the read; slow/failing DNS resolution for a dead callback
            # host can still stall well past it. Splitting the two keeps
            # this call from hanging the whole request indefinitely.
            timeout=(3, 5),
        )
    except requests.RequestException as exc:
        # Best-effort: money has already moved on our side, so we don't
        # fail the confirm request just because the notification failed.
        # But swallowing this with zero trace makes exactly this kind of
        # misconfigured-callback-URL bug invisible - log it.
        print(f"[payment] callback to {payment_request.callback_url} failed: {exc}")


@payment_bp.route("/complete")
def complete():
    """PAGE 3 — Transaction Complete. Reads from session."""
    txn = session.pop("txn", None)
    if not txn:
        return redirect(url_for("dashboard.index"))
    return render_template("transaction_complete.html", txn=txn)


# ============================================================
# Manual demo/testing pages - NOT part of the real ecommerce
# integration. Useful for showing the QR/scan concept without a
# running ecommerce app.
# ============================================================

@payment_bp.route("/qr")
def qr_demo_page():
    """Demo page: simulates the merchant side, generating a QR client-side
    with qrcode.js. Not used by the real ecommerce integration - that
    flow goes through POST /api/payment-requests instead."""
    return render_template("qr.html")


@payment_bp.route("/qr-scanner")
def qr_scanner():
    """Demo page: uses the device camera (jsQR) to scan a QR and redirect
    to /pay/<transaction_id>. Useful for testing the real flow end to end
    with your own camera instead of clicking a link."""
    return render_template("qr_scanner.html")
