# ============================================================
# routes/payment.py
# Handles the full payment flow.
#
# FRONTEND PREVIEW MODE
# ---------------------
# All database imports are commented out.
# Routes use mock data from utils/helpers.py.
# The full 3-page flow works: select → confirm → complete.
# ============================================================

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from decimal import Decimal

# These helpers now return mock data instead of DB queries
from utils.helpers import (
    get_consumer_accounts,
    get_account_by_id,
    get_merchant_by_name,
    process_payment,
)

# TODO (backend): no extra imports needed — helpers.py handles the swap

payment_bp = Blueprint("payment", __name__)


@payment_bp.route("/pay", methods=["GET"])
def select_account():
    """
    PAGE 1 — Account Selection
    Reads order_id, amount, merchant from the URL.
    Example: /pay?order_id=1001&amount=450&merchant=pageturn-books
    """
    order_id = request.args.get("order_id", "1001")       # default for easy preview
    amount   = request.args.get("amount",   "450.00")
    merchant = request.args.get("merchant", "pageturn-books")

    # Validate amount is a positive number
    try:
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= 0:
            raise ValueError
    except Exception:
        return render_template("error.html", message="Invalid payment amount."), 400

    # get_consumer_accounts() returns mock data in frontend mode
    accounts = get_consumer_accounts()

    return render_template(
        "select_account.html",
        accounts=accounts,
        order_id=order_id,
        amount=amount,
        merchant=merchant,
    )


@payment_bp.route("/pay", methods=["POST"])
def confirm_payment():
    """
    PAGE 2 — Confirm Payment
    Receives selected account_id + payment details from the form.
    """
    account_id = request.form.get("account_id")
    order_id   = request.form.get("order_id")
    amount     = request.form.get("amount")
    merchant   = request.form.get("merchant")

    if not all([account_id, order_id, amount, merchant]):
        return redirect(url_for("payment.select_account"))

    # get_account_by_id() searches mock data in frontend mode
    account = get_account_by_id(int(account_id))
    if not account:
        return redirect(url_for("payment.select_account"))

    amount_decimal = Decimal(str(amount))
    balance_after  = account.balance - amount_decimal

    return render_template(
        "confirm_payment.html",
        account=account,
        order_id=order_id,
        amount=amount_decimal,
        merchant=merchant,
        balance_after=balance_after,
    )


@payment_bp.route("/confirm-payment", methods=["POST"])
def process():
    """
    Processes the payment after "Confirm Payment" is clicked.
    In frontend mode, process_payment() simulates success without touching the DB.
    """
    account_id = request.form.get("account_id")
    order_id   = request.form.get("order_id")
    amount     = request.form.get("amount")
    merchant   = request.form.get("merchant")

    result = process_payment(
        account_id=int(account_id),
        order_id=order_id,
        amount=amount,
        merchant_name=merchant,
    )

    if not result["success"]:
        account       = get_account_by_id(int(account_id))
        amount_decimal = Decimal(str(amount))
        balance_after  = account.balance - amount_decimal
        return render_template(
            "confirm_payment.html",
            account=account,
            order_id=order_id,
            amount=amount_decimal,
            merchant=merchant,
            balance_after=balance_after,
            error=result["error"],
        )

    # Store result in session so the complete page can read it
    session["txn"] = {
        "reference": result["reference"],
        "order_id":  order_id,
        "amount":    str(amount),
        "merchant":  merchant,
    }

    return redirect(url_for("payment.complete"))


@payment_bp.route("/complete")
def complete():
    """PAGE 3 — Transaction Complete. Reads from session."""
    txn = session.pop("txn", None)

    if not txn:
        return redirect(url_for("dashboard.index"))

    return render_template("transaction_complete.html", txn=txn)


# ============================================================
# API endpoint — also works in frontend mode (returns mock response)
# TODO (backend): process_payment() will do real DB writes once enabled
# ============================================================

@payment_bp.route("/qr")
def qr_page():
    """
    QR Generator page — simulates the Merchant App side.
    Displays a form to enter order_id, amount, merchant.
    On submit, generates a real scannable QR code entirely in the browser
    using qrcode.js (no backend needed).
    The QR encodes the full payment URL:
      http://127.0.0.1:5000/pay?order_id=...&amount=...&merchant=...
    """
    return render_template("qr.html")


@payment_bp.route("/qr-scanner")
def qr_scanner():
    """
    QR Scanner page — simulates the Customer Bank App side.
    Uses the device camera (via jsQR library) to scan a QR code.
    When a valid payment QR is detected, it automatically redirects
    to /pay?order_id=...&amount=...&merchant=...
    """
    return render_template("qr_scanner.html")


@payment_bp.route("/api/pay", methods=["POST"])
def api_pay():
    """JSON API endpoint for programmatic payment triggering."""
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "No JSON body provided."}), 400

    order_id   = data.get("order_id")
    amount     = data.get("amount")
    merchant   = data.get("merchant")
    account_id = data.get("account_id")

    if not all([order_id, amount, merchant, account_id]):
        return jsonify({"success": False, "error": "Missing required fields."}), 400

    result = process_payment(
        account_id=int(account_id),
        order_id=order_id,
        amount=amount,
        merchant_name=merchant,
    )

    return jsonify(result), (200 if result["success"] else 400)
