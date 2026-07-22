# ============================================================
# utils/helpers.py
# Contains reusable helper functions and core business logic.
# Keeping logic here (separate from routes) makes code cleaner
# and easier to maintain. Routes simply call these functions.
# ============================================================

import random
import string
from decimal import Decimal

from database import db
from models import Account, Transaction


def generate_reference_number():
    """
    Generates a random alphanumeric reference number.
    Example: "TXNA3F8K2M9X"
    """
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return f"TXN{random_part}"


def get_consumer_accounts():
    """Fetches all consumer accounts from the database."""
    return Account.query.filter_by(type="consumer").all()


def get_all_accounts():
    """Fetches all accounts (consumer + merchant) for the dashboard."""
    return Account.query.order_by(Account.type, Account.name).all()


def get_account_by_id(account_id):
    """Fetches a single account by its primary key (id)."""
    return db.session.get(Account, account_id)


def get_merchant_by_name(merchant_name):
    """
    Fetches a merchant account by name.
    The Ecommerce app sends the merchant name (e.g. 'pageturn-books').
    """
    return Account.query.filter_by(name=merchant_name, type="merchant").first()


def process_payment(account_id, order_id, amount, merchant_name):
    """
    Processes a payment from a consumer to a merchant.

    Steps:
      1. Find consumer account.
      2. Find merchant account.
      3. Check sufficient balance.
      4. Deduct from consumer, add to merchant.
      5. Insert transaction record.
      6. Commit everything atomically (all-or-nothing).

    Returns:
      { "success": True,  "reference": "TXN..." }
      { "success": False, "error": "reason" }
    """
    # Use Decimal for precise financial arithmetic (never use float for money)
    amount = Decimal(str(amount))

    consumer = get_account_by_id(account_id)
    if not consumer:
        return {"success": False, "error": "Account not found."}

    merchant = get_merchant_by_name(merchant_name)
    if not merchant:
        return {"success": False, "error": f"Merchant '{merchant_name}' not found."}

    if consumer.balance < amount:
        return {"success": False, "error": "Insufficient balance."}

    try:
        # Deduct and credit balances
        consumer.balance -= amount
        merchant.balance += amount

        # Build and save the transaction record
        reference = generate_reference_number()
        txn = Transaction(
            order_id=str(order_id),
            from_account=consumer.account_number,
            to_account=merchant.account_number,
            amount=amount,
            reference_number=reference,
        )
        db.session.add(txn)

        # Commit saves all three changes atomically.
        # If anything fails, the except block rolls everything back.
        db.session.commit()

        return {"success": True, "reference": reference}

    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": f"Transaction failed: {str(e)}"}
