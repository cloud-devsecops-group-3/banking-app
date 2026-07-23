# ============================================================
# mysql/services/payment_service.py
#
# Payment Service — MySQL + SQLAlchemy Atomic Transaction
# --------------------------------------------------------
# Orchestrates the full payment flow inside a single DB transaction:
#   1. Validate consumer account exists.
#   2. Validate merchant account exists.
#   3. Verify sufficient balance.
#   4. Decrease consumer balance.
#   5. Increase merchant balance.
#   6. Create transaction record.
#   7. Commit — all three writes land together or none do.
#      On any exception, rollback is called automatically.
#
# ATOMICITY GUARANTEE
# -------------------
# All writes happen inside one db.session block wrapped in
# try/except. If anything fails (network drop, constraint
# violation, etc.) db.session.rollback() fires and MySQL
# reverts every change made in that session — no partial state.
#
# Public API (called by utils/helpers.py):
#   process_payment(account_id, order_id, amount, merchant_name)
#       -> {"success": True,  "reference": "<TXNXXX>"}
#       -> {"success": False, "error": "<reason>"}
# ============================================================

from decimal import Decimal
from database import db
from mysql.services.account_service import get_account_by_id, get_merchant_by_name
from mysql.services.transaction_service import create_transaction
from utils.generate_ref import generate_reference_number


def process_payment(
    account_id,
    order_id: str,
    amount,
    merchant_name: str,
) -> dict:
    """
    Execute a payment atomically inside a MySQL transaction.

    Args:
        account_id    : integer PK of the consumer account (may arrive as str).
        order_id      : order identifier from the QR code.
        amount        : payment amount (str / int / float / Decimal).
        merchant_name : merchant's `name` field (e.g. 'pageturn-books').

    Returns:
        {"success": True,  "reference": "<TXNXXXXXXXX>"}   on success.
        {"success": False, "error": "<human-readable msg>"} on failure.
    """
    # ── Normalise amount to Decimal for precise arithmetic ────
    try:
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= 0:
            raise ValueError
    except Exception:
        return {"success": False, "error": "Invalid payment amount."}

    # ── Validate consumer ─────────────────────────────────────
    consumer = get_account_by_id(account_id)
    if not consumer:
        return {"success": False, "error": "Account not found."}

    # ── Validate merchant ─────────────────────────────────────
    merchant = get_merchant_by_name(merchant_name)
    if not merchant:
        return {"success": False, "error": f"Merchant '{merchant_name}' not found."}

    # ── Check balance ─────────────────────────────────────────
    if consumer.balance < amount_decimal:
        return {"success": False, "error": "Insufficient balance."}

    # ── Execute atomically ────────────────────────────────────
    try:
        # Update balances in-memory — SQLAlchemy tracks these changes
        consumer.balance -= amount_decimal
        merchant.balance += amount_decimal

        # Generate unique reference number
        reference = generate_reference_number()

        # Stage transaction record (no commit yet)
        create_transaction({
            "order_id"        : order_id,
            "from_account"    : consumer.account_number,
            "to_account"      : merchant.account_number,
            "amount"          : amount_decimal,
            "reference_number": reference,
            "merchant"        : merchant_name,
        })

        # Commit — all three writes (consumer balance, merchant balance,
        # transaction row) land in MySQL together as one atomic operation.
        db.session.commit()

        return {"success": True, "reference": reference}

    except Exception as e:
        # Roll back every staged change — MySQL is left untouched
        db.session.rollback()
        return {"success": False, "error": f"Transaction failed: {str(e)}"}
