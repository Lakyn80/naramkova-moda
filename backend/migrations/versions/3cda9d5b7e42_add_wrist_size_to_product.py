"""add wrist_size to product

Revision ID: 3cda9d5b7e42
Revises: 20241212_add_variant_price_description
Create Date: 2025-12-17
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3cda9d5b7e42"
down_revision = "20241212_add_variant_price_description"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("product", schema=None) as batch_op:
        batch_op.add_column(sa.Column("wrist_size", sa.String(length=50), nullable=True))


def downgrade():
    with op.batch_alter_table("product", schema=None) as batch_op:
        batch_op.drop_column("wrist_size")
