# backend/models/order_item.py
from backend.extensions import db

class OrderItem(db.Model):
    __tablename__ = 'orderitem'
    __table_args__ = {'extend_existing': True}
    __tablename__ = "order_item"

    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)

