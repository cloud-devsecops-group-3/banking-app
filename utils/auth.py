# ============================================================
# utils/auth.py
# Two decorators controlling who can reach what:
#   - @login_required : a consumer must be logged in (session["account_id"])
#   - @admin_required : an admin must be logged in (session["is_admin"])
#   - @dashboard_required : an admin or consumer must be logged in
# ============================================================

from functools import wraps

from flask import redirect, request, session, url_for


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("account_id"):
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def dashboard_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("account_id") and not session.get("is_admin"):
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped
