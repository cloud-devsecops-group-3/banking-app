# ============================================================
# app.py
# Flask Application Factory — MySQL + SQLAlchemy Backend
# -------------------------------------------------------
# On startup:
#   1. Load config (SECRET_KEY, SQLALCHEMY_DATABASE_URI, etc.)
#   2. Initialise SQLAlchemy and bind it to the Flask app.
#   3. Create all tables in MySQL (safe to run multiple times).
#   4. Auto-seed demo accounts if the accounts table is empty.
#   5. Register route Blueprints.
#   6. Register the `currency` Jinja2 filter.
# ============================================================

from flask import Flask
from config import Config
from database import db


# ── Demo seed data ────────────────────────────────────────────
DEMO_ACCOUNTS = [
    {"name": "John Doe",        "account_number": "1234567890", "type": "consumer", "balance": 5000.00},
    {"name": "Jane Smith",      "account_number": "9876543210", "type": "consumer", "balance": 3500.00},
    {"name": "Alex Cruz",       "account_number": "4567891230", "type": "consumer", "balance": 8000.00},
    {"name": "pageturn-books",  "account_number": "1111111111", "type": "merchant", "balance": 100000.00},
]


def _auto_seed() -> None:
    """
    Insert demo accounts into MySQL if the accounts table is empty.

    Idempotent — checks each account_number before inserting.
    Runs once inside the app context at startup.
    """
    from models import Account

    print("[seed] Checking MySQL for existing accounts...")
    inserted = 0

    for data in DEMO_ACCOUNTS:
        exists = Account.query.filter_by(
            account_number=data["account_number"]
        ).first()

        if not exists:
            account = Account(
                name           = data["name"],
                account_number = data["account_number"],
                type           = data["type"],
                balance        = data["balance"],
            )
            db.session.add(account)
            inserted += 1
            print(f"[seed]   + Inserted: {data['name']} ({data['account_number']})")
        else:
            print(f"[seed]   - Skipped (exists): {data['name']} ({data['account_number']})")

    if inserted:
        db.session.commit()

    print(f"[seed] Done. {inserted} account(s) inserted.")


def create_app() -> Flask:
    app = Flask(__name__)

    # ── Load configuration ─────────────────────────────────────
    app.config.from_object(Config)

    # ── Initialise SQLAlchemy ──────────────────────────────────
    db.init_app(app)

    # ── Register Blueprints ────────────────────────────────────
    from routes.payment   import payment_bp
    from routes.dashboard import dashboard_bp
    from routes.health    import health_bp

    app.register_blueprint(payment_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(health_bp)

    # ── Jinja2 currency filter ─────────────────────────────────
    def format_currency(value):
        try:
            return f"₱{float(value):,.2f}"
        except (ValueError, TypeError):
            return value

    app.jinja_env.filters["currency"] = format_currency

    # ── Create tables + seed ───────────────────────────────────
    with app.app_context():
        db.create_all()          # CREATE TABLE IF NOT EXISTS for every model
        _auto_seed()             # insert demo data if table is empty

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
