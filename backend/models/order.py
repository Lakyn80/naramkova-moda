# backend/models/order.py
from datetime import datetime
from backend.extensions import db

class Order(db.Model):
    __tablename__ = "order"

    id = db.Column(db.Integer, primary_key=True)

    # párování plateb
    vs = db.Column(db.String(10), unique=True, index=True, nullable=True)
    total_czk = db.Column(db.Numeric(10, 2), nullable=True)
    status = db.Column(db.String(32), nullable=False, default="awaiting_payment")

    # zákazník
    customer_name = db.Column(db.String(120), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_address = db.Column(db.Text, nullable=False)
    note = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete")

    def __repr__(self):
        return f"<Order #{self.id} – {self.customer_name} – VS:{self.vs}>"
