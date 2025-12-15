"""add variant price and description

Revision ID: 20241212_add_variant_price_description
Revises: 20241211_add_variant_stock
Create Date: 2025-12-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20241212_add_variant_price_description"
down_revision = "20241211_add_variant_stock"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c["name"] for c in insp.get_columns("product_variant")}
    if "description" not in cols:
        op.add_column("product_variant", sa.Column("description", sa.Text(), nullable=True))
    if "price_czk" not in cols:
        op.add_column("product_variant", sa.Column("price_czk", sa.Numeric(10, 2), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = {c["name"] for c in insp.get_columns("product_variant")}
    if "price_czk" in cols:
        op.drop_column("product_variant", "price_czk")
    if "description" in cols:
        op.drop_column("product_variant", "description")
