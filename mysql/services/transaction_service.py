# ============================================================
# mysql/services/transaction_service.py
#
# Transaction Service — MySQL + SQLAlchemy Persistence Layer
# -----------------------------------------------------------
# Handles writing transaction records to the `transactions` table.
# Always called from inside payment_service.py within an active
# db.session — the caller is responsible for commit/rollback.
#
# Public API (called by payment_service.py):
#   create_transaction(payload) -> Transaction
# ============================================================

from datetime import datetime, timezone
from database import db
from models import Transaction


def create_transaction(payload: dict) -> Transaction:
    """
    Build and stage a Transaction record inside the current db.session.

    Does NOT commit — payment_service.py owns the commit so that
    the balance updates and the transaction record are always
    committed together atomically.

    Args:
        payload : dict with keys:
                    order_id         (str)
                    from_account     (str)  consumer account_number
                    to_account       (str)  merchant account_number
                    amount           (Decimal)
                    reference_number (str)
                    merchant         (str)  merchant name (stored for easy display)

    Returns:
        Transaction — the unsaved ORM instance (caller commits).
    """
    txn = Transaction(
        order_id         = str(payload["order_id"]),
        from_account     = str(payload["from_account"]),
        to_account       = str(payload["to_account"]),
        amount           = payload["amount"],
        reference_number = str(payload["reference_number"]),
        # transaction_date defaults to utcnow in the model definition
    )

    # Stage the record — NOT yet written to MySQL
    db.session.add(txn)

    return txn
