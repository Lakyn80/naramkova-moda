# backend/user_loader.py
from backend.extensions import login_manager
from backend.models.user import User


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None
