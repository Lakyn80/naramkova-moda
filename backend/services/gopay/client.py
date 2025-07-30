import os
from gopay import payments
from dotenv import load_dotenv

# 🟩 Načtení proměnných z .env (relativně vzhledem k této složce)
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env'))
load_dotenv(dotenv_path)

def create_gopay_client():
    print("=== 🔍 DEBUG GoPay konfigurace ===")
    print("GOID:", os.getenv('GOPAY_GOID'))
    print("CLIENT_ID:", os.getenv('GOPAY_CLIENT_ID'))
    print("CLIENT_SECRET:", os.getenv('GOPAY_CLIENT_SECRET'))
    print("GATEWAY_URL:", os.getenv('GOPAY_GATEWAY_URL'))
    print("=== ============================ ===")

    return payments({
        'goid': os.getenv('GOPAY_GOID'),
        'client_id': os.getenv('GOPAY_CLIENT_ID'),         # ✅ správně malými písmeny
        'client_secret': os.getenv('GOPAY_CLIENT_SECRET'), # ✅ správně malými písmeny
        'gateway_url': os.getenv('GOPAY_GATEWAY_URL'),     # ✅ správně malými písmeny
        'scope': 'payment-create'
    })

