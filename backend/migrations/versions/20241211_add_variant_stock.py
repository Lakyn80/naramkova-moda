"""add stock to product_variant

Revision ID: 20241211_add_variant_stock
Revises: 20241210_add_product_variant_media
Create Date: 2025-12-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "20241211_add_variant_stock"
down_revision = "20241210_add_product_variant_media"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    cols = [c["name"] for c in inspector.get_columns("product_variant")]
    if "stock" not in cols:
        op.add_column(
          "product_variant",
          sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
        )
    # SQLite neumí ALTER COLUMN DROP DEFAULT; default 0 ponecháme


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    cols = [c["name"] for c in inspector.get_columns("product_variant")]
    if "stock" in cols:
        op.drop_column("product_variant", "stock")
