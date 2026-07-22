# ============================================================
# routes/payment.py
# Handles the full payment flow using a Flask Blueprint.
#
# A Blueprint is a way to organize routes into separate files.
# This Blueprint handles: /pay (GET + POST) and /complete
#
# Flow:
#   GET  /pay               -> Show account selection page
#   POST /pay               -> Handle account selection, show confirm page
#   POST /confirm-payment   -> Process payment, redirect to complete
#   GET  /complete          -> Show transaction complete page
# ============================================================

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from utils.helpers import (
    get_consumer_accounts,
    get_account_by_id,
    get_merchant_by_name,
    process_payment,
)
from decimal import Decimal

# Create the Blueprint. "payment" is its internal name.
payment_bp = Blueprint("payment", __name__)


@payment_bp.route("/pay", methods=["GET"])
def select_account():
    """
    PAGE 1 - Account Selection
    Reads order_id, amount, and merchant from the URL query string.
    Example URL: /pay?order_id=1001&amount=450&merchant=pageturn-books
    Displays all consumer accounts as selectable cards.
    """
    # Read payment details from the URL (sent by the Ecommerce app)
    order_id = request.args.get("order_id")
    amount = request.args.get("amount")
    merchant = request.args.get("merchant")

    # Validate that all required parameters are present
    if not all([order_id, amount, merchant]):
        return render_template("error.html", message="Missing payment details. Please scan the QR code again."), 400

    # Validate that amount is a positive number
    try:
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= 0:
            raise ValueError
    except Exception:
        return render_template("error.html", message="Invalid payment amount."), 400

    # Fetch all consumer accounts to display as cards
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
    PAGE 2 - Confirm Payment
    Receives the selected account_id and payment details from the form.
    Displays a summary for the user to review before confirming.
    """
    # Read form data submitted from the account selection page
    account_id = request.form.get("account_id")
    order_id = request.form.get("order_id")
    amount = request.form.get("amount")
    merchant = request.form.get("merchant")

    if not all([account_id, order_id, amount, merchant]):
        return redirect(url_for("payment.select_account"))

    # Fetch the selected account details
    account = get_account_by_id(int(account_id))
    if not account:
        return redirect(url_for("payment.select_account"))

    amount_decimal = Decimal(str(amount))
    balance_after = account.balance - amount_decimal

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
    Processes the payment after the user clicks "Confirm Payment".
    Calls the business logic in helpers.py, then redirects to the
    complete page on success or back to confirm on failure.
    """
    account_id = request.form.get("account_id")
    order_id = request.form.get("order_id")
    amount = request.form.get("amount")
    merchant = request.form.get("merchant")

    # Run the payment logic (deduct, credit, record)
    result = process_payment(
        account_id=int(account_id),
        order_id=order_id,
        amount=amount,
        merchant_name=merchant,
    )

    if not result["success"]:
        # Re-fetch account to show updated confirm page with error
        account = get_account_by_id(int(account_id))
        amount_decimal = Decimal(str(amount))
        balance_after = account.balance - amount_decimal
        return render_template(
            "confirm_payment.html",
            account=account,
            order_id=order_id,
            amount=amount_decimal,
            merchant=merchant,
            balance_after=balance_after,
            error=result["error"],
        )

    # Store transaction details in session to display on the complete page
    session["txn"] = {
        "reference": result["reference"],
        "order_id": order_id,
        "amount": str(amount),
        "merchant": merchant,
    }

    return redirect(url_for("payment.complete"))


@payment_bp.route("/complete")
def complete():
    """
    PAGE 3 - Transaction Complete
    Reads transaction details from the session and displays the success page.
    Clears the session data after reading to prevent re-display on refresh.
    """
    txn = session.pop("txn", None)

    if not txn:
        # If someone navigates here directly without a transaction, redirect home
        return redirect(url_for("dashboard.index"))

    return render_template("transaction_complete.html", txn=txn)


# ============================================================
# API Endpoint
# POST /pay  (JSON)
# Allows the Ecommerce app to trigger payment programmatically.
# ============================================================

@payment_bp.route("/api/pay", methods=["POST"])
def api_pay():
    """
    API endpoint for programmatic payment processing.
    Accepts JSON: { "order_id": "1001", "amount": 450, "merchant": "pageturn-books", "account_id": 1 }
    Returns JSON: { "success": true, "reference": "TXN..." }
    """
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "No JSON body provided."}), 400

    order_id = data.get("order_id")
    amount = data.get("amount")
    merchant = data.get("merchant")
    account_id = data.get("account_id")

    if not all([order_id, amount, merchant, account_id]):
        return jsonify({"success": False, "error": "Missing required fields."}), 400

    result = process_payment(
        account_id=int(account_id),
        order_id=order_id,
        amount=amount,
        merchant_name=merchant,
    )

    status_code = 200 if result["success"] else 400
    return jsonify(result), status_code
