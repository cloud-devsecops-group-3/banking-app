# ============================================================
# mysql/services/account_service.py
#
# Account Service — MySQL + SQLAlchemy Persistence Layer
# -------------------------------------------------------
# All read operations against the `accounts` table live here.
# This module is the ONLY place that queries the accounts table.
#
# Public API (called by utils/helpers.py):
#   get_all_accounts()            -> list[Account]
#   get_consumer_accounts()       -> list[Account]
#   get_account_by_id(id)         -> Account | None
#   get_merchant_by_name(name)    -> Account | None
#
# Returns SQLAlchemy Account model instances directly.
# The Account model already has .id, .name, .account_number,
# .type, .balance, and .masked_account_number() — so templates
# and routes work without any changes.
#
# To switch back to Firestore:
#   • Point utils/helpers.py imports back to firebase.services.
#   • No routes or templates change.
# ============================================================

from models import Account


def get_all_accounts() -> list:
    """
    Return every account sorted by type then name.

    SQLAlchemy operation:
        SELECT * FROM accounts ORDER BY type, name

    Returns:
        list[Account] — SQLAlchemy model instances.
    """
    return (
        Account.query
        .order_by(Account.type, Account.name)
        .all()
    )


def get_consumer_accounts() -> list:
    """
    Return only consumer accounts.

    SQLAlchemy operation:
        SELECT * FROM accounts WHERE type = 'consumer'

    Returns:
        list[Account]
    """
    return (
        Account.query
        .filter_by(type="consumer")
        .all()
    )


def get_account_by_id(account_id) -> Account:
    """
    Return a single account by its integer primary key.

    SQLAlchemy operation:
        SELECT * FROM accounts WHERE id = :account_id LIMIT 1

    Args:
        account_id : integer primary key (passed as str from form — cast handled here).

    Returns:
        Account if found, None otherwise.
    """
    try:
        pk = int(account_id)
    except (TypeError, ValueError):
        return None

    return Account.query.get(pk)


def get_merchant_by_name(merchant_name: str) -> Account:
    """
    Return a merchant account by its name field.

    SQLAlchemy operation:
        SELECT * FROM accounts
        WHERE type = 'merchant' AND name = :merchant_name
        LIMIT 1

    Args:
        merchant_name : e.g. 'pageturn-books'

    Returns:
        Account if found, None otherwise.
    """
    return (
        Account.query
        .filter_by(type="merchant", name=merchant_name)
        .first()
    )
