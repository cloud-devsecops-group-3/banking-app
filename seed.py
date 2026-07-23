# ============================================================
# seed.py
# Inserts demo accounts. Called automatically by app.py at startup
# (inside its own app_context), so this never needs to be run by hand -
# same idempotent-seeding rule the ecommerce app follows.
#
# Can still be run directly for convenience:
#   python seed.py
#
# What it does:
#   Inserts demo consumer and merchant accounts (if they don't exist).
#   Table creation is handled by db.create_all() in app.py, not here.
# ============================================================

from database import db
from models import Account

# Demo accounts to seed into the database
DEMO_ACCOUNTS = [
    # Consumers
    {"name": "John Doe",     "account_number": "1234567890", "type": "consumer", "balance": 5000.00},
    {"name": "Jane Smith",   "account_number": "9876543210", "type": "consumer", "balance": 3500.00},
    {"name": "Alex Cruz",    "account_number": "4567891230", "type": "consumer", "balance": 8000.00},
    # Merchant
    {"name": "pageturn-books", "account_number": "1111111111", "type": "merchant", "balance": 100000.00},
]


def seed_accounts():
    """
    Inserts demo accounts. Skips any account whose account_number already
    exists. Must be called from inside an active app_context.
    """
    inserted = 0
    for data in DEMO_ACCOUNTS:
        exists = Account.query.filter_by(account_number=data["account_number"]).first()
        if not exists:
            account = Account(
                name=data["name"],
                account_number=data["account_number"],
                type=data["type"],
                balance=data["balance"],
            )
            db.session.add(account)
            inserted += 1
            print(f"  + Inserted: {data['name']} ({data['account_number']})")
        else:
            print(f"  - Skipped (already exists): {data['name']} ({data['account_number']})")

    db.session.commit()
    print(f"Seed complete. {inserted} account(s) inserted.")


if __name__ == "__main__":
    # Standalone run: needs its own app context since app.py isn't driving it.
    from app import create_app

    app = create_app()
    with app.app_context():
        seed_accounts()
