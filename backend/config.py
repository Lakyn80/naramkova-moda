import os

class Config:
    SECRET_KEY = "tajny_klic_zmen_si_ho"
    SQLALCHEMY_DATABASE_URI = "sqlite:///../instance/database.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ✅ Přidej toto:
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Maximální velikost uploadu 16 MB
    
    # ── Nastavení pro Flask-Mail ───────────────────────────────
    MAIL_SERVER = 'smtp.gmail.com'  # nebo smtp.seznam.cz atd.
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = '24112020ek@gmail.com'     # změň na svůj
    MAIL_PASSWORD = 'xqpjsqabachnmewc'
    MAIL_DEFAULT_SENDER = '24112020ek@gmail.com'