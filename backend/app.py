# backend/app.py
import logging
import os
import sys

# Ensure project root is on PYTHONPATH when running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Show INFO logs even outside the werkzeug access log
logging.basicConfig(level=logging.INFO)

from flask import Flask, send_from_directory
from backend.config import Config

# Extensions
from backend.extensions import db, login_manager, bcrypt, migrate, cors, init_mail

# Blueprints
from backend.admin import admin_bp
from backend.auth.login_routes import auth_bp
from backend.api.routes.product_routes import api_products
from backend.api.routes.category_routes import api_categories
from backend.api.routes.media_routes import api_media
from backend.api.routes.order_routes import order_bp
from backend.client import client_bp
from backend.api.routes.payment_routes import payment_bp
from backend.debug_routes import debug_bp
from backend import models as _models  # noqa: F401
from backend.auth import login_routes  # noqa: F401
from backend.auth import password_reset_routes  # noqa: F401


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    init_mail(app)

    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    "http://localhost:3000",
                    "http://localhost:5173",
                    "https://lakyn80.github.io",
                ],
                "supports_credentials": True,
            }
        },
    )

    login_manager.login_view = "auth.login"
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_products)
    app.register_blueprint(api_categories)
    app.register_blueprint(api_media)
    app.register_blueprint(order_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(debug_bp)

    @app.route("/favicon.ico")
    def favicon():
        fav_dir = os.path.join(app.root_path, "static")
        fav_path = os.path.join(fav_dir, "favicon.ico")
        if os.path.exists(fav_path):
            return send_from_directory(fav_dir, "favicon.ico", mimetype="image/vnd.microsoft.icon")
        return ("", 204)

    # Diagnostics: list all routes
    @app.get("/__routes")
    def __routes():
        lines = []
        for r in sorted(app.url_map.iter_rules(), key=lambda x: x.rule):
            methods = ",".join(
                sorted(m for m in r.methods if m in {"GET", "POST", "PUT", "DELETE", "PATCH"})
            )
            lines.append(f"{r.rule:35s} -> {r.endpoint} [{methods}]")
        return "<pre>" + "\n".join(lines) + "</pre>"

    # Diagnostics: mail config without password
    @app.get("/__mail_cfg")
    def __mail_cfg():
        cfg = app.config
        safe = {
            "MAIL_SERVER": cfg.get("MAIL_SERVER"),
            "MAIL_PORT": cfg.get("MAIL_PORT"),
            "MAIL_USE_SSL": cfg.get("MAIL_USE_SSL"),
            "MAIL_USE_TLS": cfg.get("MAIL_USE_TLS"),
            "MAIL_USERNAME": cfg.get("MAIL_USERNAME"),
            "MAIL_DEFAULT_SENDER": cfg.get("MAIL_DEFAULT_SENDER"),
            "MAIL_SUPPRESS_SEND": cfg.get("MAIL_SUPPRESS_SEND"),
            "MAIL_DEBUG": cfg.get("MAIL_DEBUG"),
        }
        return safe, 200

    # Optional mail ping when debugging (non-auth prefixed variant)
    if app.debug:
        from flask_mail import Message
        from backend.extensions import mail

        @app.get("/__mail_test")
        def __mail_test():
            to = app.config.get("MAIL_USERNAME")
            sender_addr = app.config.get("MAIL_DEFAULT_SENDER") or to
            msg = Message(
                subject="Mail ping (Flask)",
                recipients=[to],
                body="OK z Flasku",
                sender=("Naramkova Moda", sender_addr),
            )
            mail.send(msg)
            return "OK (mail sent)"

    return app


# For gunicorn
app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
