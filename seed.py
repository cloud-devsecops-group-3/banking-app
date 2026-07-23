# seed.py
# Creates demo accounts and the admin login.
# Called automatically by app.py at startup (idempotent).
# Can also be run directly:  python seed.py

from werkzeug.security import generate_password_hash
from database import db
from models import Account, AdminUser

DEMO_ACCOUNTS = [
    {"name": "John Doe",        "account_number": "1234567890", "type": "consumer",
     "balance": 5000.00,   "username": "jdoe",   "password": "password123"},
    {"name": "Jane Smith",      "account_number": "9876543210", "type": "consumer",
     "balance": 3500.00,   "username": "jsmith", "password": "password123"},
    {"name": "Alex Cruz",       "account_number": "4567891230", "type": "consumer",
     "balance": 8000.00,   "username": "acruz",  "password": "password123"},
    {"name": "pageturn-books",  "account_number": "1111111111", "type": "merchant",
     "balance": 100000.00, "username": None,      "password": None},
]

DEMO_ADMIN = {"username": "admin", "password": "admin123"}


def seed_accounts():
    """
    Insert demo accounts and admin user if they don't already exist.
    Must be called from inside an active Flask app_context.
    """
    inserted = 0

    for data in DEMO_ACCOUNTS:
        if not Account.query.filter_by(account_number=data["account_number"]).first():
            db.session.add(Account(
                name           = data["name"],
                account_number = data["account_number"],
                type           = data["type"],
                balance        = data["balance"],
                username       = data["username"],
                password_hash  = generate_password_hash(data["password"]) if data["password"] else None,
            ))
            inserted += 1
            print(f"  [seed] + {data['name']} ({data['account_number']})")
        else:
            print(f"  [seed] - skipped (exists): {data['name']}")

    if not AdminUser.query.filter_by(username=DEMO_ADMIN["username"]).first():
        db.session.add(AdminUser(
            username      = DEMO_ADMIN["username"],
            password_hash = generate_password_hash(DEMO_ADMIN["password"]),
        ))
        inserted += 1
        print(f"  [seed] + admin user: {DEMO_ADMIN['username']}")
    else:
        print(f"  [seed] - skipped (exists): admin user")

    db.session.commit()
    print(f"  [seed] done — {inserted} record(s) inserted.")


if __name__ == "__main__":
    # Standalone run — build a minimal app context without triggering
    # seed_accounts() a second time (app.py's create_app calls it too,
    # but here we call it ourselves after create_all).
    from flask import Flask
    from config import Config

    _app = Flask(__name__)
    _app.config.from_object(Config)
    db.init_app(_app)

    with _app.app_context():
        db.create_all()
        seed_accounts()
