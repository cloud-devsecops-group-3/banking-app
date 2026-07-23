# ============================================================
# seed.py
# Inserts demo accounts and the admin login. Called automatically by
# app.py at startup (inside its own app_context), so this never needs
# to be run by hand - same idempotent-seeding rule the ecommerce app
# follows.
#
# Can still be run directly for convenience:
#   python seed.py
#
# DEMO CREDENTIALS - these are intentionally simple, for a training
# project only. Never reuse this pattern anywhere real accounts exist.
# ============================================================

from werkzeug.security import generate_password_hash

from database import db
from models import Account, AdminUser

# Demo consumer + merchant accounts. Consumers get login credentials;
# the merchant never logs in (it's just a payee name).
DEMO_ACCOUNTS = [
    {"name": "John Doe",   "account_number": "1234567890", "type": "consumer",
     "balance": 5000.00, "username": "jdoe",   "password": "password123"},
    {"name": "Jane Smith", "account_number": "9876543210", "type": "consumer",
     "balance": 3500.00, "username": "jsmith", "password": "password123"},
    {"name": "Alex Cruz",  "account_number": "4567891230", "type": "consumer",
     "balance": 8000.00, "username": "acruz",  "password": "password123"},
    {"name": "pageturn-books", "account_number": "1111111111", "type": "merchant",
     "balance": 100000.00, "username": None, "password": None},
]

DEMO_ADMIN = {"username": "admin", "password": "admin123"}


def seed_accounts():
    """
    Inserts demo accounts and the admin login. Skips anything that
    already exists (by account_number for accounts, by username for the
    admin). Must be called from inside an active app_context.
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
                username=data["username"],
                password_hash=generate_password_hash(data["password"]) if data["password"] else None,
            )
            db.session.add(account)
            inserted += 1
            print(f"  + Inserted: {data['name']} ({data['account_number']})")
        else:
            print(f"  - Skipped (already exists): {data['name']} ({data['account_number']})")

    admin_exists = AdminUser.query.filter_by(username=DEMO_ADMIN["username"]).first()
    if not admin_exists:
        db.session.add(AdminUser(
            username=DEMO_ADMIN["username"],
            password_hash=generate_password_hash(DEMO_ADMIN["password"]),
        ))
        inserted += 1
        print(f"  + Inserted admin user: {DEMO_ADMIN['username']}")
    else:
        print(f"  - Skipped (already exists): admin user {DEMO_ADMIN['username']}")

    db.session.commit()
    print(f"Seed complete. {inserted} record(s) inserted.")


if __name__ == "__main__":
    # Standalone run: needs its own app context since app.py isn't driving it.
    from app import create_app

    app = create_app()
    with app.app_context():
        seed_accounts()
