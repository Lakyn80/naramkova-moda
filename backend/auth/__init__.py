# backend/auth/__init__.py
from backend.extensions import login_manager

# The user_loader is registered in backend.extensions to avoid circular imports.
