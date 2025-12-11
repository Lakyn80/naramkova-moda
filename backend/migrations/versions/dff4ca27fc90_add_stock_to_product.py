"""add stock to product

Revision ID: dff4ca27fc90
Revises: 7e88b1fa74bb
Create Date: 2025-09-08 11:57:30.012035

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dff4ca27fc90'
down_revision = '7e88b1fa74bb'
branch_labels = None
depends_on = None


def upgrade():
    # SQLite-safe: použijeme batch_alter_table
    with op.batch_alter_table("product", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("stock", sa.Integer(), nullable=False, server_default="1")
        )

    # Zrušíme server_default (ať se další chování řídí modelem v kódu)
    with op.batch_alter_table("product", schema=None) as batch_op:
        batch_op.alter_column("stock", server_default=None)


def downgrade():
    with op.batch_alter_table("product", schema=None) as batch_op:
        batch_op.drop_column("stock")
