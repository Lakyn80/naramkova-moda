# ✅ Tento soubor definuje model User
from backend.extensions import db, login_manager, bcrypt
from flask_login import UserMixin
from werkzeug.security import generate_password_hash as wz_generate_password_hash
from werkzeug.security import check_password_hash as wz_check_password_hash

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    # ✅ e-mail pro reset hesla (už máš po migraci)
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)

    # --- Hesla ---------------------------------------------------------------
    # Nově ukládáme přes Flask-Bcrypt, aby to sedělo s resetem hesla
    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    # Ověření: nejdřív zkus Bcrypt; když to nevyjde, zkus Werkzeuge (kvůli starým hashům)
    def check_password(self, password: str) -> bool:
        try:
            # Bcrypt umí poznat svůj formát; vrátí True/False
            if bcrypt.check_password_hash(self.password_hash, password):
                return True
        except Exception:
            # kdyby byl hash v jiném formátu, Bcrypt může vyhodit chybu → ignorujeme
            pass
        # Fallback: starý Werkzeug hash (pbkdf2:sha256:...)
        try:
            return wz_check_password_hash(self.password_hash, password)
        except Exception:
            return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f"<User {self.username} email={self.email}>"

# ✅ Načítání uživatele pro Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
