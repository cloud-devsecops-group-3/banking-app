# ============================================================
# routes/dashboard.py
# Read-only account balance dashboard.
#
# FRONTEND PREVIEW MODE
# ---------------------
# get_all_accounts() returns mock data — no DB needed.
# TODO (backend): no changes needed here once helpers.py is updated.
# ============================================================

from flask import Blueprint, render_template
from utils.helpers import get_all_accounts

# TODO (backend): no extra imports needed

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
def index():
    """Displays all accounts with current balances. Read-only."""
    accounts = get_all_accounts()
    return render_template("dashboard.html", accounts=accounts)
