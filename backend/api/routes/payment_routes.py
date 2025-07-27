# ✅ Import potřebných modulů
from flask import Blueprint, request, jsonify
from backend.services.gopay.create import create_payment  # Import funkce z modulu GoPay

# ✅ Blueprint pro platební endpoint
payment_bp = Blueprint("payment_bp", __name__)

# ✅ Route pro vytvoření platby přes GoPay
@payment_bp.route("/api/pay", methods=["POST"])
def pay():
    data = request.json  # 📥 Načteme JSON data z frontendové žádosti

    # ✅ Ověříme, že všechna potřebná pole existují
    required = ["amount", "order_number", "return_url", "product_name", "email"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # ✅ Vytvoříme platbu pomocí služby create_payment
        payment_response = create_payment(data)

        # ✅ Vrátíme odpověď GoPay do frontend
        return jsonify(payment_response), 200

    except Exception as e:
        # 🔴 Pokud dojde k chybě, vypíšeme ji do konzole pro ladění
        print("💥 Chyba při volání GoPay:", e)
        return jsonify({"error": str(e)}), 500
