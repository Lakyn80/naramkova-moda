from backend.extensions import db

class Category(db.Model):
    __tablename__ = "category"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    group = db.Column(db.String(100), nullable=True)

    products = db.relationship("Product", back_populates="category", lazy=True)

    def __repr__(self): return f"<Category {self.name}>"
