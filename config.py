# ============================================================
# config.py
# Loads all configuration from environment variables.
# Flask reads this class to configure the application.
# ============================================================

import os
from dotenv import load_dotenv

# Load the .env file into environment variables
load_dotenv()


class Config:
    """Central configuration class. Flask reads these attributes to configure itself."""

    # Secret key signs session cookies. Set a strong random value in production.
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-dev-key")

    # Build the SQLAlchemy database URI from individual env variables.
    # Format: mysql+pymysql://user:password@host:port/database
    _DB_HOST = os.getenv("DB_HOST", "localhost")
    _DB_PORT = os.getenv("DB_PORT", "3306")
    _DB_NAME = os.getenv("DB_NAME", "banking_db")
    _DB_USER = os.getenv("DB_USER", "root")
    _DB_PASSWORD = os.getenv("DB_PASSWORD", "")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{_DB_USER}:{_DB_PASSWORD}@{_DB_HOST}:{_DB_PORT}/{_DB_NAME}"
    )
    # SQLALCHEMY_DATABASE_URI = "sqlite:///bank.db"

    # Disable SQLAlchemy event notifications to save memory
    SQLALCHEMY_TRACK_MODIFICATIONS = False
