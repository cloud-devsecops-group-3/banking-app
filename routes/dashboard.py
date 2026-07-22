# ============================================================
# routes/dashboard.py
# Handles the read-only account balance dashboard.
#
# Blueprint route: /dashboard
# Purpose: Let users verify account balances after a payment.
# No editing, adding, or deleting — read only.
# ============================================================

from flask import Blueprint, render_template
from utils.helpers import get_all_accounts

# Create the Blueprint named "dashboard"
dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
def index():
    """
    Displays all accounts (consumer + merchant) with their current balances.
    This is read-only — no forms, no buttons to modify data.
    """
    accounts = get_all_accounts()
    return render_template("dashboard.html", accounts=accounts)
