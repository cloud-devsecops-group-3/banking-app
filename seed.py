# ============================================================
# seed.py
# Creates database tables and inserts demo accounts.
#
# This script is IDEMPOTENT — running it multiple times will
# never create duplicate records. It checks before inserting.
#
# How to run:
#   python seed.py
#
# What it does:
#   1. Creates all tables defined in models.py (if they don't exist)
#   2. Inserts demo consumer and merchant accounts (if they don't exist)
# ============================================================

from app import create_app
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


def seed():
    """
    Creates tables and inserts demo accounts.
    Skips any account whose account_number already exists in the database.
    """
    app = create_app()

    with app.app_context():
        # Create all tables defined in models.py.
        # db.create_all() is safe to run multiple times — it skips existing tables.
        print("Creating tables...")
        db.create_all()
        print("Tables ready.")

        # Insert each demo account only if it doesn't already exist
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

        # Commit all new inserts at once
        db.session.commit()
        print(f"\nSeed complete. {inserted} account(s) inserted.")


if __name__ == "__main__":
    seed()
