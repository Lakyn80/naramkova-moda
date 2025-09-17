from datetime import datetime
from backend.extensions import db

class Payment(db.Model):
    __tablename__ = "payment"

    id = db.Column(db.Integer, primary_key=True)
    vs = db.Column(db.String(32), index=True, nullable=False)
    amount_czk = db.Column(db.Numeric(10, 2), nullable=False)
    reference = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(32), default="received")  # received | matched
    received_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Payment VS:{self.vs} {self.amount_czk} CZK>"
