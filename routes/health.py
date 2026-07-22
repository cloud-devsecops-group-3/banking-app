# ============================================================
# routes/health.py
# Provides a simple health check endpoint.
#
# GET /health -> returns { "status": "UP" } with HTTP 200
#
# Used by Docker, load balancers, or monitoring tools to verify
# the application is running and responsive.
# ============================================================

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/health")
def health_check():
    """Returns a simple JSON response confirming the app is running."""
    return jsonify({"status": "UP"}), 200
