# ============================================================
# utils/helpers.py
#
# Application Helpers — Service Layer Facade
# -------------------------------------------
# The ONLY module that routes import for data access.
# Delegates all database operations to mysql/services/.
#
# CURRENT BACKEND: MySQL + SQLAlchemy
#
# To switch back to Firestore:
#   Replace the mysql.services imports below with the
#   equivalent firebase.services imports — nothing else changes.
#
# Public API (called by routes):
#   generate_reference_number()
#   get_consumer_accounts()         -> list[Account]
#   get_all_accounts()              -> list[Account]
#   get_account_by_id(account_id)   -> Account | None
#   get_merchant_by_name(name)      -> Account | None
#   process_payment(...)            -> dict
# ============================================================

# ── Pure utility (no DB dependency) ──────────────────────────
# Lives in its own module to avoid circular imports.
from utils.generate_ref import generate_reference_number  # noqa: F401 — re-exported

# ── MySQL service layer ───────────────────────────────────────
# To swap to Firestore, replace these four lines with:
#   from firebase.services.account_service import (
#       get_all_accounts as _get_all_accounts, ...
#   )
#   from firebase.services.payment_service import process_payment as _process_payment
from mysql.services.account_service import (
    get_all_accounts      as _get_all_accounts,
    get_consumer_accounts as _get_consumer_accounts,
    get_account_by_id     as _get_account_by_id,
    get_merchant_by_name  as _get_merchant_by_name,
)
from mysql.services.payment_service import (
    process_payment as _process_payment,
)


# ── Public wrappers ───────────────────────────────────────────
# Thin pass-throughs so routes never import service modules directly.

def get_consumer_accounts() -> list:
    """Return all consumer accounts from MySQL."""
    return _get_consumer_accounts()


def get_all_accounts() -> list:
    """Return all accounts sorted by type then name from MySQL."""
    return _get_all_accounts()


def get_account_by_id(account_id):
    """Return a single account by its integer primary key."""
    return _get_account_by_id(account_id)


def get_merchant_by_name(merchant_name: str):
    """Return a merchant account by name."""
    return _get_merchant_by_name(merchant_name)


def process_payment(account_id, order_id: str, amount, merchant_name: str) -> dict:
    """
    Process a payment atomically against MySQL.

    Returns:
        {"success": True,  "reference": "<TXNXXXXXXXX>"}
        {"success": False, "error":     "<reason>"}
    """
    return _process_payment(
        account_id=account_id,
        order_id=order_id,
        amount=amount,
        merchant_name=merchant_name,
    )
