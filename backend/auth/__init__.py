# backend/auth/__init__.py

# Vezmeme existující blueprint z login_routes,
# aby app.py (které registruje blueprint z login_routes) a všechny další moduly
# používaly JEDEN a ten samý objekt.
from . import login_routes as _login


# Export pro zbytek balíčku: package-level auth_bp ukazuje na tentýž objekt
auth_bp = _login.auth_bp

# Pouhý import připojí view funkce k auth_bp
from . import password_reset_routes  # noqa: F401
