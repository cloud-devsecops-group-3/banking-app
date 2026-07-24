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
    _DB_HOST     = os.getenv("DB_HOST",     "10.0.2.112")
    _DB_PORT     = os.getenv("DB_PORT",     "3306")
    _DB_NAME     = os.getenv("DB_NAME",     "bankdb")
    _DB_USER     = os.getenv("DB_USER",     "bankuser")
    _DB_PASSWORD = os.getenv("DB_PASSWORD", "devpass")

    # mysql+pymysql://user:password@host:port/database
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{_DB_USER}:{_DB_PASSWORD}"
        f"@{_DB_HOST}:{_DB_PORT}/{_DB_NAME}"
    )

    BANKING_PUBLIC_BASE = os.getenv("BANKING_PUBLIC_BASE", "http://54.211.30.30.nip.io").rstrip("/")

    # Disable SQLAlchemy modification tracking (saves memory)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Keep connections alive across requests to the remote VM
    # (avoids "MySQL server has gone away" on idle connections)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping"  : True,   # test connection before using it
        "pool_recycle"   : 280,    # recycle connections every 280 s
        "connect_args"   : {"connect_timeout": 10},
    }
