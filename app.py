# ============================================================
# app.py
# Main entry point of the Flask application.
# ============================================================

import os

from flask import Flask

from config import Config
from database import db


def create_app(config_overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)

    # --------------------------------------------------------
    # Register Blueprints (route files)
    # --------------------------------------------------------
    from routes.payment import payment_bp
    from routes.dashboard import dashboard_bp
    from routes.health import health_bp

    app.register_blueprint(payment_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(health_bp)

    # --------------------------------------------------------
    # Custom Jinja2 filter: {{ value | currency }}
    # Formats a number as Philippine Peso: 5000 -> ₱5,000.00
    # --------------------------------------------------------
    def format_currency(value):
        try:
            return f"₱{float(value):,.2f}"
        except (ValueError, TypeError):
            return value

    app.jinja_env.filters["currency"] = format_currency

    with app.app_context():
        db.create_all()
        from seed import seed_accounts

        seed_accounts()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)), debug=True)
