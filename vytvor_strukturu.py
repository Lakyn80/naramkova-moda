import os

# Hlavní složka
project_root = "backend"

folders = [
    os.path.join(project_root, "admin"),
    os.path.join(project_root, "client"),
    os.path.join(project_root, "auth"),
    os.path.join(project_root, "services"),
    os.path.join(project_root, "static", "uploads"),
    os.path.join(project_root, "templates", "admin", "products"),
    os.path.join(project_root, "templates", "client"),
]

files = {
    os.path.join(project_root, "app.py"): "",
    os.path.join(project_root, "config.py"): "",
    os.path.join(project_root, "database.py"): "",
    os.path.join(project_root, "extensions.py"): "",
    os.path.join(project_root, "create_admin.py"): "",
    os.path.join(project_root, "admin", "__init__.py"): "",
    os.path.join(project_root, "admin", "routes.py"): "",
    os.path.join(project_root, "admin", "models.py"): "",
    os.path.join(project_root, "client", "__init__.py"): "",
    os.path.join(project_root, "client", "routes.py"): "",
    os.path.join(project_root, "auth", "__init__.py"): "",
    os.path.join(project_root, "auth", "login_routes.py"): "",
    os.path.join(project_root, "services", "__init__.py"): "",
}

# Vytvoření složek
for folder in folders:
    os.makedirs(folder, exist_ok=True)

# Vytvoření souborů
for filepath, content in files.items():
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ Projektová struktura vytvořena.")
