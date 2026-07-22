# ============================================================
# app.py
# Main entry point of the Flask application.
#
# FRONTEND PREVIEW MODE
# ---------------------
# Database initialization is commented out.
# The app runs with static mock data — no MySQL needed.
# To re-enable the database later, uncomment the marked lines.
# ============================================================

from flask import Flask

# TODO (backend): uncomment these when database is ready
# from config import Config
# from database import db


def create_app():
    app = Flask(__name__)

    # TODO (backend): load config and init DB when ready
    # app.config.from_object(Config)
    # db.init_app(app)

    # Secret key is still needed for Flask sessions (used on complete page)
    app.secret_key = "frontend-preview-secret-key"

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

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
