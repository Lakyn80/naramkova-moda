from datetime import datetime
from backend.extensions import db  # ✅ OPRAVENO – správný import z backendu


# ─── Category model ───────────────────────────────────────────────
class Category(db.Model):
    """
    Reprezentuje kategorii produktů.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    group = db.Column(db.String(100), nullable=True)  # ✅ Nové pole pro skupinu (Rodina, Svatba...)

    products = db.relationship("Product", backref="category", lazy=True)

    def __repr__(self) -> str:
        return f"<Category {self.name}>"

    def to_dict(self):
        """
        Vrací data kategorie pro JSON API.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "group": self.group
        }


# ─── Product model ────────────────────────────────────────────────
class Product(db.Model):
    """
    Reprezentuje produkt v e-shopu.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    price_czk = db.Column(db.Numeric(10, 2), nullable=False)
    image = db.Column(db.String(255), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    media = db.relationship(
        "ProductMedia",
        backref="product",
        lazy=True,
        cascade="all, delete"
    )

    def __repr__(self) -> str:
        return f"<Product {self.name}>"


# ─── ProductMedia model ──────────────────────────────────────────
class ProductMedia(db.Model):
    """
    Jeden obrázek nebo video připojený k produktu.
    """
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    media_type = db.Column(db.String(20), nullable=False)  # "image" nebo "video"
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)

    def __repr__(self) -> str:
        return f"<ProductMedia {self.media_type} - {self.filename}>"

# ─── Order model ──────────────────────────────────────────────────
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_address = db.Column(db.Text, nullable=False)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete")

    def __repr__(self):
        return f"<Order #{self.id} – {self.customer_name}>"


# ─── OrderItem model ──────────────────────────────────────────────
class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
