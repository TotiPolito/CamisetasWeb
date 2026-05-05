from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.services.auth_service import (
    authenticate_admin,
    get_login_lock_state,
    is_admin_logged_in,
    register_failed_login,
    reset_login_attempts,
    validate_csrf_token,
)


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def login():
    if is_admin_logged_in():
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        if not validate_csrf_token(request.form.get("csrf_token")):
            flash("La sesion del formulario vencio. Intenta de nuevo.", "error")
            return redirect(url_for("auth.login"))

        lock_state = get_login_lock_state()
        if lock_state["is_blocked"]:
            flash(
                f"Demasiados intentos fallidos. Espera {lock_state['remaining_seconds']} segundos antes de volver a intentar.",
                "error",
            )
            return redirect(url_for("auth.login"))

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = authenticate_admin(username, password)

        if admin:
            session.clear()
            session["admin_id"] = admin["id"]
            reset_login_attempts()
            flash("Sesion iniciada correctamente.", "success")
            return redirect(url_for("admin.dashboard"))

        register_failed_login()
        flash("Usuario o contrasena incorrectos.", "error")

    return render_template("admin/login.html", page_name="login")


@auth_bp.post("/admin/logout")
def logout():
    if not validate_csrf_token(request.form.get("csrf_token")):
        flash("No se pudo cerrar la sesion por un token invalido.", "error")
        return redirect(url_for("admin.dashboard"))

    session.clear()
    return redirect(url_for("public.home"))
