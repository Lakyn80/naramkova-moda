# 📁 backend/config.py
import os
from dotenv import load_dotenv

# Načtení .env proměnných ze souboru v backend/
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# ✅ Cesta k databázi uvnitř složky backend/instance/
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

# ⚠️ DŮLEŽITÉ: na Windows převést backslashe na forward slashe pro SQLAlchemy URI
DB_PATH = os.path.join(INSTANCE_DIR, "database.db")
DB_URI = "sqlite:///" + DB_PATH.replace("\\", "/")

class Config:
    # ✅ Použijeme absolutní, „posix“ URI – to řeší chybu „unable to open database file“
    SQLALCHEMY_DATABASE_URI = DB_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "super-secret-key"

    # ✅ Upload složka pro média (a pojistka na existenci)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # ✅ Načti e-mail údaje z .env
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME)
