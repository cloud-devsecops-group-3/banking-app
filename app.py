# app.py
# Flask application factory.
# Connects to MySQL, creates tables, seeds demo data, registers blueprints.

import os
from flask import Flask
from config import Config
from database import db


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    # ── Blueprints ─────────────────────────────────────────────
    from routes.auth      import auth_bp
    from routes.payment   import payment_bp
    from routes.dashboard import dashboard_bp
    from routes.health    import health_bp

    app.register_blueprint(auth_bp)
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

    # ── Create tables + seed demo data ─────────────────────────
    # Wrapped in try/except so a temporary DB outage prints a clear
    # warning instead of crashing the whole process at startup.
    with app.app_context():
        try:
            db.create_all()          # CREATE TABLE IF NOT EXISTS for every model
            from seed import seed_accounts
            seed_accounts()
        except Exception as exc:
            print(f"[startup] WARNING: could not reach database — {exc}")
            print("[startup] App will still start; DB calls will fail until the DB is reachable.")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)), debug=True)
