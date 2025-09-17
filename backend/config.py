# 📁 backend/config.py
import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

def _env(key: str, default=None):
    v = os.getenv(key)
    return v if v not in (None, "", "None") else default

def _env_bool(key: str, default: bool = False) -> bool:
    v = os.getenv(key)
    if v in (None, "", "None"):
        return default
    return str(v).strip().lower() in ("1", "true", "t", "yes", "y", "on")

def _resolve_sqlite_uri(db_url: str | None) -> str:
    if not db_url:
        db_path = os.path.join(INSTANCE_DIR, "database.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return "sqlite:///" + db_path.replace("\\", "/")

    if db_url.startswith("sqlite:///"):
        raw_path = db_url.replace("sqlite:///", "", 1)
        if not os.path.isabs(raw_path):
            raw_path = os.path.join(BASE_DIR, raw_path)
        db_path = os.path.normpath(raw_path)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return "sqlite:///" + db_path.replace("\\", "/")

    return db_url

class Config:
    SECRET_KEY = _env("SECRET_KEY", "dev-please-change-me")

    SQLALCHEMY_DATABASE_URI = _resolve_sqlite_uri(_env("DATABASE_URL"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = False  # ✅ JSON výstup v UTF-8 (emoji se neescapují)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

    # >>> SHODA S TESTEM
    MAIL_SERVER = _env("MAIL_SERVER", "smtp.seznam.cz")
    MAIL_PORT = int(_env("MAIL_PORT", 465))
    MAIL_USE_SSL = _env_bool("MAIL_USE_SSL", True)
    MAIL_USE_TLS = _env_bool("MAIL_USE_TLS", False)
    MAIL_USERNAME = _env("MAIL_USERNAME")
    MAIL_PASSWORD = _env("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = _env("MAIL_DEFAULT_SENDER", _env("MAIL_USERNAME"))
    MAIL_SUPPRESS_SEND = _env_bool("MAIL_SUPPRESS_SEND", False)
    MAIL_DEBUG = _env_bool("MAIL_DEBUG", True)

    PASSWORD_RESET_SALT = _env("PASSWORD_RESET_SALT", "nm-password-reset")
    PASSWORD_RESET_SUBJECT = _env("PASSWORD_RESET_SUBJECT", "Obnova hesla – Náramková Móda")

    MERCHANT_IBAN = _env("MERCHANT_IBAN")
