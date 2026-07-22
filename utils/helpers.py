# ============================================================
# utils/helpers.py
#
# FRONTEND PREVIEW MODE
# ---------------------
# All database calls are commented out.
# Functions return static mock data so the UI can be previewed
# without a MySQL connection.
#
# To restore real DB logic later, uncomment the marked sections
# and remove the mock return statements below them.
# ============================================================

import random
import string
from decimal import Decimal

# TODO (backend): uncomment when database is ready
# from database import db
# from models import Account, Transaction


# ── Static mock data ────────────────────────────────────────
# Simulates what would normally come from the database.
# Each dict mirrors the columns of the Account model.

class MockAccount:
    """
    A simple object that mimics an SQLAlchemy Account model instance.
    Used so templates can call account.name, account.balance, etc.
    exactly the same way they will with real data.
    """
    def __init__(self, id, name, account_number, type, balance):
        self.id             = id
        self.name           = name
        self.account_number = account_number
        self.type           = type
        self.balance        = Decimal(str(balance))

    def masked_account_number(self):
        """Returns account number with all but last 4 digits masked. e.g. ••••7890"""
        return "••••" + self.account_number[-4:]


# Static list of mock accounts — mirrors seed.py data
MOCK_ACCOUNTS = [
    MockAccount(1, "John Doe",        "1234567890", "consumer", 5000.00),
    MockAccount(2, "Jane Smith",      "9876543210", "consumer", 3500.00),
    MockAccount(3, "Alex Cruz",       "4567891230", "consumer", 8000.00),
    MockAccount(4, "pageturn-books",  "1111111111", "merchant", 100000.00),
]
# ────────────────────────────────────────────────────────────


def generate_reference_number():
    """Generates a random alphanumeric reference number. e.g. TXNA3F8K2M9X"""
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return f"TXN{random_part}"


def get_consumer_accounts():
    """
    Returns all consumer accounts.

    FRONTEND MODE: returns mock data.
    TODO (backend): replace with ->
        return Account.query.filter_by(type="consumer").all()
    """
    return [a for a in MOCK_ACCOUNTS if a.type == "consumer"]


def get_all_accounts():
    """
    Returns all accounts sorted by type then name.

    FRONTEND MODE: returns mock data.
    TODO (backend): replace with ->
        return Account.query.order_by(Account.type, Account.name).all()
    """
    return sorted(MOCK_ACCOUNTS, key=lambda a: (a.type, a.name))


def get_account_by_id(account_id):
    """
    Returns a single account by its ID.

    FRONTEND MODE: searches mock list.
    TODO (backend): replace with ->
        return db.session.get(Account, account_id)
    """
    for account in MOCK_ACCOUNTS:
        if account.id == account_id:
            return account
    return None


def get_merchant_by_name(merchant_name):
    """
    Returns a merchant account by name.

    FRONTEND MODE: searches mock list.
    TODO (backend): replace with ->
        return Account.query.filter_by(name=merchant_name, type="merchant").first()
    """
    for account in MOCK_ACCOUNTS:
        if account.name == merchant_name and account.type == "merchant":
            return account
    return None


def process_payment(account_id, order_id, amount, merchant_name):
    """
    Simulates processing a payment.

    FRONTEND MODE: does NOT touch any database.
    Just validates the mock data and returns a fake reference number
    so the full UI flow (select → confirm → complete) can be tested.

    TODO (backend): replace the body with real DB logic:
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
            consumer.balance -= amount
            merchant.balance += amount
            reference = generate_reference_number()
            txn = Transaction(
                order_id=str(order_id),
                from_account=consumer.account_number,
                to_account=merchant.account_number,
                amount=amount,
                reference_number=reference,
            )
            db.session.add(txn)
            db.session.commit()
            return {"success": True, "reference": reference}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": f"Transaction failed: {str(e)}"}
    """
    amount = Decimal(str(amount))

    # Validate consumer exists in mock data
    consumer = get_account_by_id(account_id)
    if not consumer:
        return {"success": False, "error": "Account not found."}

    # Validate merchant exists in mock data
    merchant = get_merchant_by_name(merchant_name)
    if not merchant:
        return {"success": False, "error": f"Merchant '{merchant_name}' not found."}

    # Check sufficient balance (works on mock Decimal balances)
    if consumer.balance < amount:
        return {"success": False, "error": "Insufficient balance."}

    # Return a fake success — no DB write happens in frontend mode
    return {"success": True, "reference": generate_reference_number()}
