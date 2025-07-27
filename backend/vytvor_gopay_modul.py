import os

# 📁 Vytvoříme složku ve správné cestě v rámci backendu
base_dir = os.path.join(os.getcwd(), "services", "gopay")

# 🧾 Soubory s jejich obsahem
files = {
    "__init__.py": "# __init__.py - dělá ze složky gopay modul\n",
    "client.py": '''from gopay import payments

def create_gopay_client():
    return payments({
        'goid': '1234567890',  # ← Nahraď svým testovacím GoID
        'clientId': 'your-client-id',
        'clientSecret': 'your-client-secret',
        'gatewayUrl': 'https://gw.sandbox.gopay.com/api',
        'scope': 'payment-create'
    })
''',
    "create.py": '''from .client import create_gopay_client

def create_payment(order_data):
    gopay = create_gopay_client()
    payment = gopay.create_payment(order_data)
    return payment
'''
}

# 🛠️ Vytvoříme složky a soubory
os.makedirs(base_dir, exist_ok=True)
for filename, content in files.items():
    path = os.path.join(base_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ Složka 'services/gopay' vytvořena s moduly: __init__.py, client.py, create.py")
