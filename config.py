# ============================================================
# config.py
# Application Configuration
# --------------------------
# Loads all settings from environment variables (via .env).
# Builds the SQLAlchemy connection URI from individual DB_* vars.
# ============================================================

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Flask ────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    FLASK_ENV  = os.getenv("FLASK_ENV", "development")
    DEBUG      = FLASK_ENV == "development"

    # ── MySQL connection ──────────────────────────────────────
    # No hardcoded host default. If DB_HOST isn't set, fall back to a
    # local SQLite file (matches the ecommerce app's config.py and the
    # behavior documented in this repo's README). Every real environment
    # (docker compose, EC2, k8s, ...) must set DB_HOST explicitly.
    _DB_HOST     = os.getenv("DB_HOST")
    _DB_PORT     = os.getenv("DB_PORT",     "3306")
    _DB_NAME     = os.getenv("DB_NAME",     "bankdb")
    _DB_USER     = os.getenv("DB_USER",     "bankuser")
    _DB_PASSWORD = os.getenv("DB_PASSWORD", "devpass")

    if _DB_HOST:
        # mysql+pymysql://user:password@host:port/database
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{_DB_USER}:{_DB_PASSWORD}"
            f"@{_DB_HOST}:{_DB_PORT}/{_DB_NAME}"
        )
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///banking.db"

    # Public, phone/browser-reachable base URL for this app. Used to build
    # the QR image src shown on the ecommerce order-status page. Must be
    # set explicitly per environment (e.g. http://<EC2_PUBLIC_IP>:5001) -
    # no environment-specific IP is baked in here anymore.
    BANKING_PUBLIC_BASE = os.getenv("BANKING_PUBLIC_BASE", "").rstrip("/")

    # Disable SQLAlchemy modification tracking (saves memory)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Keep connections alive across requests to the remote VM
    # (avoids "MySQL server has gone away" on idle connections).
    # connect_timeout is a PyMySQL-only keyword - passing it to sqlite3
    # raises TypeError, not a connection error, so it must only be set
    # on the MySQL branch.
    if _DB_HOST:
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_pre_ping"  : True,   # test connection before using it
            "pool_recycle"   : 280,    # recycle connections every 280 s
            "connect_args"   : {"connect_timeout": 10},
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {}
