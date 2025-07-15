# 📁 backend/client/routes.py

from flask import Blueprint, request, jsonify
from backend.extensions import db
from backend.admin.models import Order, OrderItem, Product
from backend.api.utils.email import send_email

client_bp = Blueprint("client", __name__)  # nebo "client_bp"


@client_bp.route("/api/orders", methods=["POST"])
def create_order():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    address = data.get("address")
    note = data.get("note")
    items = data.get("items", [])

    # ✅ 1. Uložení objednávky do DB
    order = Order(
        customer_name=name,
        customer_email=email,
        customer_address=address,
        note=note
    )
    db.session.add(order)
    db.session.flush()  # získáme order.id pro OrderItem

    # ✅ 2. Uložení položek + smazání produktů z DB
    for item in items:
        # Přidání položky objednávky
        order_item = OrderItem(
            order_id=order.id,
            product_name=item["name"],
            quantity=item["quantity"],
            price=item["price"]
        )
        db.session.add(order_item)

        # Smazání produktu z databáze (jedinečné produkty)
        product = Product.query.filter_by(name=item["name"]).first()
        if product:
            db.session.delete(product)

    db.session.commit()

    # ✅ 3. Odeslání e-mailu zákazníkovi
    customer_message = f"""Děkujeme za objednávku, {name}!

Adresa:
{address}

Poznámka: {note or "—"}

Objednané položky:
""" + "\n".join([f"- {item['name']} × {item['quantity']}" for item in items])

    send_email("Potvrzení objednávky", [email], customer_message)

    # ✅ 4. E-mail adminovi
    admin_message = f"""📦 Nová objednávka od {name} ({email}):

Adresa:
{address}

Poznámka: {note or "—"}

Objednávka:
""" + "\n".join([f"- {item['name']} × {item['quantity']} ks" for item in items])

    send_email("📦 Nová objednávka", ["tvuj@email.cz"], admin_message)

    return jsonify({"message": "Objednávka uložena a potvrzena."}), 200
