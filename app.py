# ============================================================
# app.py
# The main entry point of the Flask application.
#
# This file:
#   1. Creates the Flask app instance
#   2. Loads configuration from config.py
#   3. Initializes the database (SQLAlchemy)
#   4. Registers all Blueprints (route groups)
#   5. Registers a custom Jinja2 filter for currency formatting
#   6. Starts the development server when run directly
#
# Flask is a micro web framework. It receives HTTP requests,
# routes them to the correct function, and returns HTML responses.
# ============================================================

from flask import Flask
from config import Config
from database import db


def create_app():
    """
    Application factory function.
    Creates and configures the Flask app.
    Using a factory function makes the app easier to test and extend.
    """

    # Create the Flask application instance.
    # __name__ tells Flask where to find templates and static files.
    app = Flask(__name__)

    # Load all configuration (database URI, secret key, etc.) from config.py
    app.config.from_object(Config)

    # Initialize SQLAlchemy with the Flask app.
    # This connects the `db` object (from database.py) to this app instance.
    db.init_app(app)

    # --------------------------------------------------------
    # Register Blueprints
    # Blueprints are groups of related routes defined in separate files.
    # Registering them here plugs them into the main app.
    # --------------------------------------------------------
    from routes.payment import payment_bp
    from routes.dashboard import dashboard_bp
    from routes.health import health_bp

    app.register_blueprint(payment_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(health_bp)

    # --------------------------------------------------------
    # Custom Jinja2 filter: format_currency
    # Jinja2 is the template engine Flask uses.
    # Filters let you transform values inside HTML templates.
    # Usage in template: {{ account.balance | currency }}
    # --------------------------------------------------------
    def format_currency(value):
        """Formats a number as Philippine Peso. Example: 5000 -> ₱5,000.00"""
        try:
            return f"₱{float(value):,.2f}"
        except (ValueError, TypeError):
            return value

    app.jinja_env.filters["currency"] = format_currency

    return app


# Create the app instance (used by Gunicorn in production)
app = create_app()


if __name__ == "__main__":
    # This block only runs when you execute: python app.py
    # In production, Gunicorn calls create_app() directly.
    app.run(debug=True, host="0.0.0.0", port=5000)
