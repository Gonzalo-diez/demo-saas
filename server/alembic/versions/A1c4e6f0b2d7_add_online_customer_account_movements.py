"""add online customer account movements (historial/saldo online)

Revision ID: a1c4e6f0b2d7
Revises: f7b8c9d0e1a2, d5e3a7c1f9b2
Create Date: 2026-08-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c4e6f0b2d7'
down_revision: Union[str, Sequence[str], None] = ('f7b8c9d0e1a2', 'd5e3a7c1f9b2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Saldo cacheado en online_customers ---
    op.add_column(
        'online_customers',
        sa.Column(
            'current_balance',
            sa.Numeric(12, 2),
            nullable=False,
            server_default='0.00',
        ),
    )

    # --- online_customer_account_movements ---
    op.create_table(
        'online_customer_account_movements',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('online_customer_id', sa.Integer(), sa.ForeignKey('online_customers.id'), nullable=False, index=True),
        sa.Column('movement_type', sa.String(length=50), nullable=False, index=True),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('balance_before', sa.Numeric(12, 2), nullable=False),
        sa.Column('balance_after', sa.Numeric(12, 2), nullable=False),
        sa.Column('reference_type', sa.String(length=50), nullable=True, index=True),
        sa.Column('reference_id', sa.Integer(), nullable=True, index=True),
        sa.Column('payment_method', sa.String(length=30), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('online_customer_account_movements')
    op.drop_column('online_customers', 'current_balance')