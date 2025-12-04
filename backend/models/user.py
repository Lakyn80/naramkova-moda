# backend/models/user.py
from backend.extensions import db, bcrypt
from flask_login import UserMixin
from werkzeug.security import check_password_hash as wz_check_password_hash


class User(db.Model, UserMixin):
    __tablename__ = "user"
    __table_args__ = {"extend_existing": True}  # keep to avoid duplicate table definition issues

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)

    # --- Password handling ---------------------------------------------------
    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        try:
            if bcrypt.check_password_hash(self.password_hash, password):
                return True
        except Exception:
            pass  # allow fallback to older Werkzeug hashes
        try:
            return wz_check_password_hash(self.password_hash, password)
        except Exception:
            return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f"<User {self.username} email={self.email}>"
