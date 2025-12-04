# backend/extensions.py
from __future__ import annotations

import socket
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_cors import CORS
from flask_mail import Mail

# Keep extension instances in one place to avoid circular imports
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
migrate = Migrate()
cors = CORS()
mail = Mail()


@login_manager.user_loader
def load_user(user_id):
    # Lazy import to avoid circular dependency when loading the model
    from backend.models.user import User
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None


def _coerce_bool(v, default=False) -> bool:
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in ("1", "true", "t", "yes", "y", "on")


def _clean_hostname(server: str | None) -> str:
    """Return hostname without scheme/path/spaces."""
    s = (server or "").strip()
    if "://" in s:
        s = s.split("://", 1)[1]
    if "/" in s:
        s = s.split("/", 1)[0]
    return s


def init_mail(app):
    """
    Initialize Flask-Mail with a bit of config sanitization to avoid
    'getaddrinfo failed' errors from malformed MAIL_SERVER.
    """
    cfg = app.config

    # 1) hostname
    server = _clean_hostname(cfg.get("MAIL_SERVER"))
    if not server:
        server = "smtp.seznam.cz"
        cfg["MAIL_SERVER"] = server
        app.logger.warning("MAIL_SERVER was not set -> using fallback 'smtp.seznam.cz'.")

    # 2) SSL/TLS coherence
    use_ssl = _coerce_bool(cfg.get("MAIL_USE_SSL"), False)
    use_tls = _coerce_bool(cfg.get("MAIL_USE_TLS"), False)
    if use_ssl and use_tls:
        use_tls = False
        cfg["MAIL_USE_TLS"] = False
        app.logger.info("MAIL_USE_SSL and MAIL_USE_TLS were True -> disabling TLS (prefer SSL).")

    # 3) port
    port_raw = cfg.get("MAIL_PORT")
    try:
        port = int(port_raw)
    except (TypeError, ValueError):
        port = 465 if use_ssl else (587 if use_tls else 25)
        cfg["MAIL_PORT"] = port
        app.logger.info(f"MAIL_PORT was invalid -> setting {port} (SSL={use_ssl}, TLS={use_tls}).")

    # 4) default sender
    if not cfg.get("MAIL_DEFAULT_SENDER"):
        cfg["MAIL_DEFAULT_SENDER"] = cfg.get("MAIL_USERNAME")

    # 5) quick DNS check
    try:
        infos = socket.getaddrinfo(server, cfg.get("MAIL_PORT") or 0, proto=socket.IPPROTO_TCP)
        ips = sorted({i[4][0] for i in infos if i[4]})
        if not ips:
            app.logger.warning(f"DNS resolve for '{server}' returned no IP addresses.")
    except Exception as e:
        app.logger.error(f"DNS resolve failed for MAIL_SERVER='{server}': {e}")

    # 6) final log
    app.logger.info(
        "MAIL cfg -> server=%s port=%s ssl=%s tls=%s sender=%s user=%s",
        cfg.get("MAIL_SERVER"),
        cfg.get("MAIL_PORT"),
        bool(cfg.get("MAIL_USE_SSL")),
        bool(cfg.get("MAIL_USE_TLS")),
        cfg.get("MAIL_DEFAULT_SENDER"),
        cfg.get("MAIL_USERNAME"),
    )

    mail.init_app(app)
