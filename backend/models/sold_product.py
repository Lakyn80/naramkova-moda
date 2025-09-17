# backend/models/sold_product.py
from datetime import datetime
from backend.extensions import db

class SoldProduct(db.Model):
    __tablename__ = "sold_product"

    id = db.Column(db.Integer, primary_key=True)
    original_product_id = db.Column(db.Integer)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(255), nullable=True)
    price = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    customer_name = db.Column(db.String(100))
    customer_email = db.Column(db.String(100))
    customer_address = db.Column(db.Text)
    note = db.Column(db.Text)
    payment_type = db.Column(db.String(50))
    sold_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SoldProduct {self.name} – {self.customer_name}>"
