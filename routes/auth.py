# ============================================================
# routes/auth.py
# Login is shared between consumers and the admin - same form, we just
# check which table the username matches. On success:
#   - consumer -> session["account_id"]
#   - admin    -> session["is_admin"] = True
# Never both at once (session.clear() before setting either).
# ============================================================

from flask import Blueprint, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from models import Account, AdminUser

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    next_url = request.values.get("next") or url_for("dashboard.index")

    if request.method == "GET":
        return render_template("login.html", next_url=next_url)

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    account = Account.query.filter_by(username=username, type="consumer").first()
    if account and account.password_hash and check_password_hash(account.password_hash, password):
        session.clear()
        session["account_id"] = account.id
        return redirect(next_url)

    admin = AdminUser.query.filter_by(username=username).first()
    if admin and check_password_hash(admin.password_hash, password):
        session.clear()
        session["is_admin"] = True
        return redirect(next_url)

    return render_template("login.html", next_url=next_url, error="Invalid username or password."), 401


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
