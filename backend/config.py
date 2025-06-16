import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "tajny_klic"
    # databáze leží v instance/database.db
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "instance", "database.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # kam ukládat uploady
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "backend", "static", "uploads")
