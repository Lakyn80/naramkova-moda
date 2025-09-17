# backend/extensions.py
from __future__ import annotations

import socket
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_cors import CORS
from flask_mail import Mail

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
migrate = Migrate()
cors = CORS()
mail = Mail()


def _coerce_bool(v, default=False) -> bool:
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in ("1", "true", "t", "yes", "y", "on")


def _clean_hostname(server: str | None) -> str:
    """Nechá čistý hostname – bez schématu, bez cesty, bez mezer."""
    s = (server or "").strip()
    if "://" in s:
        s = s.split("://", 1)[1]
    # odřízni případnou cestu za lomítkem
    if "/" in s:
        s = s.split("/", 1)[0]
    return s


def init_mail(app):
    """
    Inicializace Flask-Mail s drobnou sanitizací configu, aby se vyhnulo
    chybě 'getaddrinfo failed' při špatném MAIL_SERVER.
    """
    cfg = app.config

    # 1) hostname
    server = _clean_hostname(cfg.get("MAIL_SERVER"))
    if not server:
        # fallback – Seznam
        server = "smtp.seznam.cz"
        cfg["MAIL_SERVER"] = server
        app.logger.warning("MAIL_SERVER nebyl nastaven – používám fallback 'smtp.seznam.cz'.")

    # 2) SSL/TLS koherence
    use_ssl = _coerce_bool(cfg.get("MAIL_USE_SSL"), False)
    use_tls = _coerce_bool(cfg.get("MAIL_USE_TLS"), False)
    if use_ssl and use_tls:
        # současně nedává smysl – preferujeme SSL (typický Seznam)
        use_tls = False
        cfg["MAIL_USE_TLS"] = False
        app.logger.info("MAIL_USE_SSL i MAIL_USE_TLS byly True – vypínám TLS (preferuji SSL).")

    # 3) port
    port_raw = cfg.get("MAIL_PORT")
    try:
        port = int(port_raw)
    except (TypeError, ValueError):
        port = 465 if use_ssl else (587 if use_tls else 25)
        cfg["MAIL_PORT"] = port
        app.logger.info(f"MAIL_PORT byl neplatný – nastavuji {port} (SSL={use_ssl}, TLS={use_tls}).")

    # 4) default sender
    if not cfg.get("MAIL_DEFAULT_SENDER"):
        cfg["MAIL_DEFAULT_SENDER"] = cfg.get("MAIL_USERNAME")

    # 5) rychlá DNS kontrola – ať hned vidíš, kde to padá
    try:
        infos = socket.getaddrinfo(server, cfg.get("MAIL_PORT") or 0, proto=socket.IPPROTO_TCP)
        ips = sorted({i[4][0] for i in infos if i[4]})
        if not ips:
            app.logger.warning(f"DNS resolve pro '{server}' nevrátil IP adresy.")
    except Exception as e:
        app.logger.error(f"DNS resolve selhal pro MAIL_SERVER='{server}': {e}")

    # 6) finální log
    app.logger.info(
        "MAIL cfg → server=%s port=%s ssl=%s tls=%s sender=%s user=%s",
        cfg.get("MAIL_SERVER"),
        cfg.get("MAIL_PORT"),
        bool(cfg.get("MAIL_USE_SSL")),
        bool(cfg.get("MAIL_USE_TLS")),
        cfg.get("MAIL_DEFAULT_SENDER"),
        cfg.get("MAIL_USERNAME"),
    )

    mail.init_app(app)
