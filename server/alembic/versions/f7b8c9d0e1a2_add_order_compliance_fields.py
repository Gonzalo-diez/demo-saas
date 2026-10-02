"""add order compliance fields (dni, age_confirmed, tax_id, person_type, iva_condition)

Revision ID: f7b8c9d0e1a2
Revises: e1a2b3c4d5f6
Create Date: 2026-08-13 00:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7b8c9d0e1a2'
down_revision: Union[str, None] = 'e1a2b3c4d5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('customer_dni', sa.String(length=20), nullable=True))
    op.add_column(
        'orders',
        sa.Column(
            'age_confirmed',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
        ),
    )
    op.add_column('orders', sa.Column('customer_tax_id', sa.String(length=20), nullable=True))
    op.add_column('orders', sa.Column('customer_person_type', sa.String(length=20), nullable=True))
    op.add_column('orders', sa.Column('customer_iva_condition', sa.String(length=30), nullable=True))

    op.create_index(
        op.f('ix_orders_customer_tax_id'),
        'orders',
        ['customer_tax_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_orders_customer_tax_id'), table_name='orders')
    op.drop_column('orders', 'customer_iva_condition')
    op.drop_column('orders', 'customer_person_type')
    op.drop_column('orders', 'customer_tax_id')
    op.drop_column('orders', 'age_confirmed')
    op.drop_column('orders', 'customer_dni')