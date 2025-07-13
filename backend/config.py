import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "tajny_klic"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "instance", "database.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ✅ Opravená cesta k uploadům
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
