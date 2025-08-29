import os
from dotenv import load_dotenv

# Načti .env z backend/
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Instance dir (SQLite soubor)
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

def _env(key: str, default=None):
    v = os.getenv(key)
    return v if v not in (None, "", "None") else default

def _resolve_sqlite_uri(db_url: str | None) -> str:
    """
    Vrátí SQLITE URI s ABSOLUTNÍ cestou a vytvoří parent složku.
    - Pokud db_url je None → použij backend/instance/database.db
    - Pokud db_url začíná sqlite:/// a obsahuje ABSOLUTNÍ cestu → použij ji
    - Pokud db_url začíná sqlite:/// a je RELATIVNÍ → přepočítej relativní na BASE_DIR
    - Jinak (Postgres/MySQL) vrátí db_url beze změny
    """
    if not db_url:
        db_path = os.path.join(INSTANCE_DIR, "database.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return "sqlite:///" + db_path.replace("\\", "/")

    if db_url.startswith("sqlite:///"):
        raw_path = db_url.replace("sqlite:///", "", 1)
        # pokud není absolutní, udělej ji relativně k backend/
        if not os.path.isabs(raw_path):
            raw_path = os.path.join(BASE_DIR, raw_path)
        db_path = os.path.normpath(raw_path)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return "sqlite:///" + db_path.replace("\\", "/")

    # jiný typ DB (např. Postgres)
    return db_url

class Config:
    # ✅ Unicode JSON výstup (emoji a diakritika bez \u escape)
    JSON_AS_ASCII = False

    # 🔐 Secret
    SECRET_KEY = _env("SECRET_KEY", "dev-please-change-me")

    # 🗄️ Databáze (robustní vyřešení SQLite cesty)
    SQLALCHEMY_DATABASE_URI = _resolve_sqlite_uri(_env("DATABASE_URL"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 📂 Uploady
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

    # 📧 E-mail
    MAIL_SERVER = _env("MAIL_SERVER")
    MAIL_PORT = int(_env("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = _env("MAIL_USERNAME")
    MAIL_PASSWORD = _env("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = _env("MAIL_DEFAULT_SENDER", _env("MAIL_USERNAME"))

    # 💳 IBAN pro QR platby
    MERCHANT_IBAN = _env("MERCHANT_IBAN")
