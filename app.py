# app.py
# Flask application factory.
# Connects to MySQL, creates tables, seeds demo data, registers blueprints.

import os
import time
from flask import Flask
from sqlalchemy.exc import OperationalError
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
    # MySQL in a sibling container often isn't accepting connections yet
    # by the time this container starts (first-run init, slow EC2 disk,
    # etc.). Retry with backoff instead of giving up after one attempt.
    # If every attempt fails we raise — Docker's restart policy (or the
    # orchestrator) will retry the whole container rather than us running
    # forever with tables that were never created and quietly failing
    # every request. Silently continuing here was the root cause of the
    # banking app "having no tables" while looking healthy.
    max_attempts = int(os.environ.get("DB_INIT_MAX_ATTEMPTS", 10))
    retry_delay = float(os.environ.get("DB_INIT_RETRY_SECONDS", 3))

    with app.app_context():
        for attempt in range(1, max_attempts + 1):
            try:
                db.create_all()      # CREATE TABLE IF NOT EXISTS for every model
                from seed import seed_accounts
                seed_accounts()
                break
            except OperationalError as exc:
                # Genuine "can't reach the DB yet" — worth retrying.
                print(f"[startup] DB not ready (attempt {attempt}/{max_attempts}): {exc}")
                if attempt == max_attempts:
                    print("[startup] Giving up — database never became reachable.")
                    raise
                time.sleep(retry_delay)
            # Anything else (bad config, bad SQL, wrong driver kwargs, ...)
            # is a bug, not a timing issue — fail immediately instead of
            # retrying something that will never succeed.

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)), debug=True)
