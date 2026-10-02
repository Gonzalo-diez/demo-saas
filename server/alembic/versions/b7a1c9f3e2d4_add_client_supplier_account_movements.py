"""add client and supplier account movements (cuentas corrientes)

Revision ID: b7a1c9f3e2d4
Revises: fcf86696d73c
Create Date: 2026-07-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7a1c9f3e2d4'
down_revision: Union[str, None] = 'fcf86696d73c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Saldo cacheado en clients y suppliers ---
    op.add_column(
        'clients',
        sa.Column(
            'current_balance',
            sa.Numeric(12, 2),
            nullable=False,
            server_default='0.00',
        ),
    )
    op.add_column(
        'suppliers',
        sa.Column(
            'current_balance',
            sa.Numeric(12, 2),
            nullable=False,
            server_default='0.00',
        ),
    )

    # --- client_account_movements ---
    op.create_table(
        'client_account_movements',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('client_id', sa.Integer(), sa.ForeignKey('clients.id'), nullable=False, index=True),
        sa.Column('movement_type', sa.String(length=50), nullable=False, index=True),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('balance_before', sa.Numeric(12, 2), nullable=False),
        sa.Column('balance_after', sa.Numeric(12, 2), nullable=False),
        sa.Column('reference_type', sa.String(length=50), nullable=True, index=True),
        sa.Column('reference_id', sa.Integer(), nullable=True, index=True),
        sa.Column('payment_method', sa.String(length=30), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('sales_reps.id'), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- supplier_account_movements ---
    op.create_table(
        'supplier_account_movements',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('supplier_id', sa.Integer(), sa.ForeignKey('suppliers.id'), nullable=False, index=True),
        sa.Column('movement_type', sa.String(length=50), nullable=False, index=True),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('balance_before', sa.Numeric(12, 2), nullable=False),
        sa.Column('balance_after', sa.Numeric(12, 2), nullable=False),
        sa.Column('reference_type', sa.String(length=50), nullable=True, index=True),
        sa.Column('reference_id', sa.Integer(), nullable=True, index=True),
        sa.Column('payment_method', sa.String(length=30), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('sales_reps.id'), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('supplier_account_movements')
    op.drop_table('client_account_movements')
    op.drop_column('suppliers', 'current_balance')
    op.drop_column('clients', 'current_balance')
