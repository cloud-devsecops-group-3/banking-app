# ============================================================
# database.py
# Creates the single SQLAlchemy instance shared across the app.
#
# SQLAlchemy is an ORM (Object Relational Mapper) — it lets you
# work with database tables as Python classes instead of raw SQL.
#
# We create `db` here and import it in models.py and app.py
# to avoid circular imports.
# ============================================================

from flask_sqlalchemy import SQLAlchemy

# This object is attached to the Flask app in app.py via db.init_app(app)
db = SQLAlchemy()
