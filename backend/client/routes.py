# ✅ BACKEND - CLIENT ROUTES
# 📁 backend/client/routes.py

from flask import Blueprint, request, jsonify
from backend.extensions import db
from backend.admin.models import Product, Order, OrderItem, SoldProduct  # ✅ správné modely
from backend.api.utils.email import send_email                           # ✅ správný import e-mailu
from datetime import datetime

client_bp = Blueprint("client_bp", __name__)

# ------------------------------
# API: Získání všech produktů
# ------------------------------
@client_bp.route("/api/products", methods=["GET"])
def get_products():
    products = Product.query.all()
    result = []
    for product in products:
        result.append({
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price_czk": float(product.price_czk),
            "image": product.image,
            "category": product.category.name if product.category else None,
            "created_at": product.created_at.isoformat()
        })
    return jsonify(result)


# ------------------------------
# API: Vytvoření objednávky
# ------------------------------
@client_bp.route("/api/orders", methods=["POST"])
def create_order():
    data = request.get_json()

    # ✅ Získání zákaznických údajů z přesných klíčů z frontendu
    name = data.get("name")                     # frontend posílá "name"
    email = data.get("email")                   # frontend posílá "email"
    address = data.get("address")               # frontend posílá "address"
    note = data.get("note", "")                 # poznámka je volitelná
    payment_type = data.get("payment_type", "")  # může být prázdné
    cart_items = data.get("items", [])          # položky košíku

    # ✅ Validace vstupu – pokud chybí povinná pole, vrátíme chybu
    if not all([name, email, address]) or not cart_items:
        return jsonify({"error": "Chybí povinné údaje"}), 400

    # ✅ Vytvoření objednávky
    order = Order(
        customer_name=name,
        customer_email=email,
        customer_address=address,
        note=note
    )
    db.session.add(order)
    db.session.flush()  # získáme ID objednávky

    # ✅ Pro každou položku vytvoříme OrderItem + SoldProduct
    for item in cart_items:
        product_name = item.get("name")
        quantity = item.get("quantity", 1)
        price = item.get("price")

        # Najdeme produkt podle názvu (abychom našli i ID pro mazání/sold)
        product = Product.query.filter_by(name=product_name).first()
        if product:
            # 🔸 OrderItem
            order_item = OrderItem(
                product_name=product.name,
                quantity=quantity,
                price=product.price_czk,
                order=order
            )
            db.session.add(order_item)

            # 🔸 SoldProduct
            sold = SoldProduct(
                original_product_id=product.id,
                name=product.name,
                description=product.description,
                image=product.image,
                price=str(product.price_czk),
                quantity=quantity,
                customer_name=name,
                customer_email=email,
                customer_address=address,
                note=note,
                payment_type=payment_type,
                sold_at=datetime.utcnow()
            )
            db.session.add(sold)

            # ❌ Smazání z aktivních produktů
            db.session.delete(product)

    db.session.commit()

    # ✅ Odeslání e-mailu
    try:
        send_email(email, name, cart_items)
    except Exception as e:
        print(f"[CHYBA E-MAILU] {e}")

    return jsonify({"message": "Objednávka úspěšně vytvořena."}), 201
