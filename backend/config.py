import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "tajny_klic_zmen_si_ho"

    # ✅ správná cesta k databázi
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 📁 složka pro nahrané soubory
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # 📧 nastavení pro Flask-Mail
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = '24112020ek@gmail.com'
    MAIL_PASSWORD = 'xqpjsqabachnmewc'
    MAIL_DEFAULT_SENDER = '24112020ek@gmail.com'
