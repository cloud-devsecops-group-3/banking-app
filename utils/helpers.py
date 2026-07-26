# ============================================================
# utils/helpers.py
#
# Real database-backed versions of the account/payment helpers.
# (Frontend-preview mock data has been removed now that the DB is wired up.)
# ============================================================

import random
import string
from decimal import Decimal

from database import db
from models import Account, Transaction, PaymentRequest
from sqlalchemy import or_


def generate_reference_number():
    """Generates a random alphanumeric reference number. e.g. TXNA3F8K2M9X"""
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return f"TXN{random_part}"


def get_consumer_accounts():
    """Returns all consumer accounts."""
    return Account.query.filter_by(type="consumer").all()


def get_all_accounts():
    """Returns all accounts sorted by type then name."""
    return Account.query.order_by(Account.type, Account.name).all()

def get_transactions_for_account(account_number, limit=20):
    return (Transaction.query
            .filter(or_(Transaction.from_account == account_number,
                        Transaction.to_account == account_number))
            .order_by(Transaction.transaction_date.desc())
            .limit(limit).all())

def get_payment_requests_for_merchant(merchant_name, limit=20):
    return (PaymentRequest.query
            .filter_by(merchant_account=merchant_name)
            .order_by(PaymentRequest.created_at.desc())
            .limit(limit).all())

def get_account_by_id(account_id):
    """Returns a single account by its ID."""
    return db.session.get(Account, account_id)


def get_merchant_by_name(merchant_name):
    """Returns a merchant account by name."""
    return Account.query.filter_by(name=merchant_name, type="merchant").first()


def process_payment(account_id, payment_request):
    """
    Settles a payment. `payment_request` is the authoritative PaymentRequest
    row (amount, merchant_account, order_id all come from THIS, never from
    a URL or form field) - the caller only supplies which consumer account
    the user picked.

    Does the debit + credit + Transaction record as one atomic DB
    transaction: either all three happen, or none do.
    """
    consumer = get_account_by_id(account_id)
    if not consumer or consumer.type != "consumer":
        return {"success": False, "error": "Account not found."}

    merchant = get_merchant_by_name(payment_request.merchant_account)
    if not merchant:
        return {"success": False, "error": f"Merchant '{payment_request.merchant_account}' not found."}

    amount = Decimal(str(payment_request.amount))
    consumer_balance = Decimal(str(consumer.balance))
    if consumer_balance < amount:
        return {"success": False, "error": "Insufficient balance."}

    try:
        consumer.balance = consumer_balance - amount
        merchant.balance = Decimal(str(merchant.balance)) + amount
        reference = generate_reference_number()
        txn = Transaction(
            order_id=payment_request.order_id,
            from_account=consumer.account_number,
            to_account=merchant.account_number,
            amount=amount,
            reference_number=reference,
        )
        db.session.add(txn)
        db.session.commit()
        return {"success": True, "reference": reference, "account": consumer}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": f"Transaction failed: {str(e)}"}
