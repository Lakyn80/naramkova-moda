# backend/user_loader.py
from extensions import login_manager
from models.user import User

@login_manager.user_loader
def load_user(user_id: str):
    """Vrátí uživatele podle uloženého ID."""
    return User.query.get(int(user_id))
