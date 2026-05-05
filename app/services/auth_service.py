import secrets
import time
from functools import wraps

from flask import current_app, flash, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.models.admin_model import create_admin, find_admin_by_id, find_admin_by_username


def get_csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(24)
        session["_csrf_token"] = token
    return token


def validate_csrf_token(submitted_token):
    stored_token = session.get("_csrf_token")
    if not submitted_token or not stored_token:
        return False
    return secrets.compare_digest(submitted_token, stored_token)


def is_admin_logged_in():
    return bool(session.get("admin_id"))


def get_current_admin():
    admin_id = session.get("admin_id")
    if not admin_id:
        return None
    return find_admin_by_id(admin_id)


def authenticate_admin(username, password):
    admin = find_admin_by_username(username)
    if not admin:
        return None
    if not check_password_hash(admin["password_hash"], password):
        return None
    return admin


def get_login_lock_state():
    attempt_count = int(session.get("login_attempt_count", 0))
    blocked_until = int(session.get("login_block_until", 0))
    now = int(time.time())
    is_blocked = blocked_until > now
    remaining_seconds = max(0, blocked_until - now)
    return {
        "attempt_count": attempt_count,
        "blocked_until": blocked_until,
        "is_blocked": is_blocked,
        "remaining_seconds": remaining_seconds,
    }


def register_failed_login():
    state = get_login_lock_state()
    next_count = state["attempt_count"] + 1
    session["login_attempt_count"] = next_count

    if next_count >= current_app.config["LOGIN_MAX_ATTEMPTS"]:
        session["login_block_until"] = int(time.time()) + current_app.config["LOGIN_BLOCK_SECONDS"]
        session["login_attempt_count"] = 0


def reset_login_attempts():
    session.pop("login_attempt_count", None)
    session.pop("login_block_until", None)


def ensure_default_admin():
    username = str(current_app.config.get("DEFAULT_ADMIN_USERNAME") or "").strip()
    password = str(current_app.config.get("DEFAULT_ADMIN_PASSWORD") or "")

    if not username or not password:
        return

    if find_admin_by_username(username):
        return

    create_admin(username, generate_password_hash(password))


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not is_admin_logged_in():
            flash("Necesitas iniciar sesion para entrar al panel admin.", "error")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped_view
