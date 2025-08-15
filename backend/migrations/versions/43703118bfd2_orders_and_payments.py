"""orders and payments (idempotent / safe)

Revision ID: 43703118bfd2
Revises: 29044e73de5e
Create Date: 2025-08-14
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '43703118bfd2'
down_revision = '29044e73de5e'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # --- ORDER TABLE ---
    cols = {c['name'] for c in insp.get_columns('order')}

    # 1) vs
    if 'vs' not in cols:
        with op.batch_alter_table('order', schema=None) as batch_op:
            batch_op.add_column(sa.Column('vs', sa.String(length=32), nullable=True))

    # 2) total_czk
    if 'total_czk' not in cols:
        with op.batch_alter_table('order', schema=None) as batch_op:
            batch_op.add_column(sa.Column('total_czk', sa.Numeric(10, 2), nullable=True))

    # 3) status (nejdřív nullable se server_default, pak naplnit a zpřísnit)
    if 'status' not in cols:
        with op.batch_alter_table('order', schema=None) as batch_op:
            batch_op.add_column(sa.Column('status', sa.String(length=32), nullable=True, server_default='awaiting_payment'))
        op.execute('UPDATE "order" SET status = COALESCE(status, \'awaiting_payment\')')
        with op.batch_alter_table('order', schema=None) as batch_op:
            batch_op.alter_column('status', existing_type=sa.String(length=32), nullable=False)
    else:
        # kdyby sloupec existoval a byl NULL, doplníme hodnoty (bez změny typu)
        op.execute('UPDATE "order" SET status = COALESCE(status, \'awaiting_payment\')')

    # 4) index na vs (vytvořit jen pokud neexistuje)
    existing_order_indexes = {ix['name'] for ix in insp.get_indexes('order')}
    if 'ix_order_vs' not in existing_order_indexes:
        op.create_index('ix_order_vs', 'order', ['vs'], unique=False)
    # Pozn.: unikátní omezení na VS lze přidat později (až budeš chtít):
    # op.create_unique_constraint('uq_order_vs', 'order', ['vs'])

    # --- PAYMENT TABLE ---
    tables = set(insp.get_table_names())
    if 'payment' not in tables:
        op.create_table(
            'payment',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('vs', sa.String(length=32), nullable=False),
            sa.Column('amount_czk', sa.Numeric(10, 2), nullable=False),
            sa.Column('reference', sa.String(length=255), nullable=True),
            sa.Column('status', sa.String(length=32), nullable=True, server_default='received'),
            sa.Column('received_at', sa.DateTime(), nullable=True),
        )
        op.create_index('ix_payment_vs', 'payment', ['vs'], unique=False)
    else:
        # pokud tabulka existuje, zajistíme index
        existing_payment_indexes = {ix['name'] for ix in insp.get_indexes('payment')}
        if 'ix_payment_vs' not in existing_payment_indexes:
            op.create_index('ix_payment_vs', 'payment', ['vs'], unique=False)


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # --- PAYMENT ---
    tables = set(insp.get_table_names())
    if 'payment' in tables:
        existing_payment_indexes = {ix['name'] for ix in insp.get_indexes('payment')}
        if 'ix_payment_vs' in existing_payment_indexes:
            op.drop_index('ix_payment_vs', table_name='payment')
        op.drop_table('payment')

    # --- ORDER ---
    existing_order_indexes = {ix['name'] for ix in insp.get_indexes('order')}
    if 'ix_order_vs' in existing_order_indexes:
        op.drop_index('ix_order_vs', table_name='order')

    cols = {c['name'] for c in insp.get_columns('order')}
    with op.batch_alter_table('order', schema=None) as batch_op:
        if 'status' in cols:
            batch_op.drop_column('status')
        if 'total_czk' in cols:
            batch_op.drop_column('total_czk')
        if 'vs' in cols:
            batch_op.drop_column('vs')
