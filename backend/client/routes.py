from flask import Blueprint, request, jsonify
from backend.api.utils.email import send_email

client_bp = Blueprint("client", __name__)  # nebo "client_bp"

@client_bp.route("/api/orders", methods=["POST"])
def create_order():
    data = request.json
    customer_email = data.get("email")
    customer_name = data.get("name")
    items = data.get("items", [])

    # 💾 Tady můžeš časem uložit objednávku do databáze

    # E-mail zákazníkovi
    customer_message = f"Děkujeme za objednávku, {customer_name}!\n\nObsah:\n"
    for item in items:
        customer_message += f"- {item['name']} x {item['quantity']}\n"
    send_email("Potvrzení objednávky", [customer_email], customer_message)

    # E-mail adminovi
    admin_message = f"Nová objednávka od {customer_name} ({customer_email}):\n\n"
    for item in items:
        admin_message += f"- {item['name']} x {item['quantity']}\n"
    send_email("📦 Nová objednávka", ["tvuj@email.cz"], admin_message)

    return jsonify({"message": "Objednávka přijata."}), 200
