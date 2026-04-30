from flask import Flask, render_template

from config import Config
from app.controllers.admin_controller import admin_bp
from app.controllers.auth_controller import auth_bp
from app.controllers.public_controller import public_bp
from app.models.database import initialize_database
from app.services.auth_service import get_csrf_token, get_current_admin, is_admin_logged_in
from app.services.catalog_service import seed_catalog_if_empty


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    initialize_database(app)

    with app.app_context():
        seed_catalog_if_empty()

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    @app.context_processor
    def inject_template_context():
        return {
            "csrf_token": get_csrf_token,
            "current_admin": get_current_admin(),
            "is_admin_logged_in": is_admin_logged_in(),
        }

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html", page_name="error"), 404

    @app.errorhandler(400)
    def bad_request(_error):
        return render_template("errors/400.html", page_name="error"), 400

    return app
