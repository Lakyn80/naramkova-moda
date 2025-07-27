# backend/services/gopay/create.py
from .client import create_gopay_client
import json  # 🟩 potřebné pro dekódování JSON z bytes

def create_payment(data):
    gopay = create_gopay_client()

    amount_in_cents = int(data["amount"] * 100)

    payment_data = {
        "payer": {
            "allowed_payment_instruments": ["PAYMENT_CARD"],
            "default_payment_instrument": "PAYMENT_CARD",
            "contact": {
                "email": data["email"]
            }
        },
        "amount": amount_in_cents,
        "currency": "CZK",
        "order_number": data["order_number"],
        "order_description": data["product_name"],
        "callback": {
            "return_url": data["return_url"],
            "notification_url": data["return_url"] + "/notify"
        },
        "items": [
            {
                "name": data["product_name"],
                "amount": amount_in_cents,
                "count": 1
            }
        ]
    }

    response = gopay.create_payment(payment_data)

    # ✅ Bezpečný převod odpovědi na slovník
    try:
        if hasattr(response, "json") and callable(response.json):
            json_data = response.json()
            # Pokud .json() vrací bytes, dekóduj
            if isinstance(json_data, bytes):
                return json.loads(json_data.decode("utf-8"))
            return json_data
        elif isinstance(response, bytes):
            return json.loads(response.decode("utf-8"))
        elif isinstance(response, dict):
            return response
        else:
            return {"raw_response": str(response)}
    except Exception as e:
        # 🟥 Pokud selže převod, vrátíme text chyby
        return {"error": f"Chyba při zpracování odpovědi GoPay: {str(e)}"}
