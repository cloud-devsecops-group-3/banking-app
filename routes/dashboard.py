# ============================================================
# routes/dashboard.py
# Read-only account balance dashboard - admin only.
# ============================================================

from flask import Blueprint, abort, render_template, session

from utils.auth import dashboard_required
from utils.helpers import get_account_by_id, get_all_accounts

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@dashboard_required
def index():
    """Displays all balances to admins and only the owner's balance to consumers."""
    is_admin = bool(session.get("is_admin"))
    accounts = get_all_accounts() if is_admin else [get_account_by_id(session["account_id"])]
    return render_template("dashboard.html", accounts=accounts, is_admin=is_admin)

@dashboard_bp.route("/dashboard/accounts/<int:account_id>")
@dashboard_required
def account_detail(account_id):
    is_admin = bool(session.get("is_admin"))
    if not is_admin and session.get("account_id") != account_id:
        abort(403)