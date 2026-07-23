# config.py
# Loads all configuration from environment variables (.env).

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-dev-key")

    _DB_HOST     = os.getenv("DB_HOST",     "10.0.1.80")
    _DB_PORT     = os.getenv("DB_PORT",     "3306")
    _DB_NAME     = os.getenv("DB_NAME",     "bankdb")
    _DB_USER     = os.getenv("DB_USER",     "bankuser")
    _DB_PASSWORD = os.getenv("DB_PASSWORD", "devpass")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{_DB_USER}:{_DB_PASSWORD}"
        f"@{_DB_HOST}:{_DB_PORT}/{_DB_NAME}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # pool_pre_ping  : test connection before each use (prevents "gone away" errors)
    # pool_recycle   : recycle connections every 280 s
    # connect_timeout: fail fast if the DB host is unreachable
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle" : 280,
        "connect_args" : {"connect_timeout": 10},
    }
