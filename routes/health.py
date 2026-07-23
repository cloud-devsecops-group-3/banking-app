# ============================================================
# routes/health.py
# Health Check Endpoint
# ----------------------
# GET /health
#
# Verifies MySQL connectivity by running a lightweight query.
# Returns HTTP 200 {"status": "UP",   "database": "MySQL Connected"}
# Returns HTTP 503 {"status": "DOWN", "database": "Disconnected"}
# ============================================================

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/health")
def health_check():
    """
    Runs a SELECT 1 against MySQL to confirm the connection is alive.
    Works even when the accounts table is empty.
    """
    try:
        from database import db
        from sqlalchemy import text

        # Cheapest possible round-trip — just checks the connection
        db.session.execute(text("SELECT 1"))

        return jsonify({
            "status"  : "UP",
            "database": "MySQL Connected",
        }), 200

    except Exception as exc:
        print(f"[health] MySQL check failed: {exc}")
        return jsonify({
            "status"  : "DOWN",
            "database": "Disconnected",
        }), 503
