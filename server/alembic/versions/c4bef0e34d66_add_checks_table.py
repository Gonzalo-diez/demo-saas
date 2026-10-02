"""add checks table

Revision ID: c4bef0e34d66
Revises: 935c3d0b21f9
Create Date: 2026-09-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c4bef0e34d66'
down_revision: Union[str, None] = '935c3d0b21f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'checks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('direction', sa.String(length=10), nullable=False),
        sa.Column('check_number', sa.String(length=50), nullable=False),
        sa.Column('bank_name', sa.String(length=100), nullable=True),
        sa.Column('drawer_name', sa.String(length=255), nullable=True),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('issue_date', sa.Date(), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pendiente', nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=True),
        sa.Column('supplier_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('pending_allocations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('client_account_movement_id', sa.Integer(), nullable=True),
        sa.Column('supplier_account_movement_id', sa.Integer(), nullable=True),
        sa.Column('deposited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("direction IN ('received', 'issued')", name='ck_check_direction'),
        sa.CheckConstraint(
            "status IN ('pendiente', 'depositado', 'acreditado', 'rechazado')",
            name='ck_check_status',
        ),
        sa.CheckConstraint(
            "(direction = 'received' AND client_id IS NOT NULL AND supplier_id IS NULL) "
            "OR (direction = 'issued' AND supplier_id IS NOT NULL AND client_id IS NULL)",
            name='ck_check_direction_matches_owner',
        ),
        sa.CheckConstraint("amount > 0", name='ck_check_amount_positive'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['sales_reps.id'], ),
        sa.ForeignKeyConstraint(
            ['client_account_movement_id'], ['client_account_movements.id'], ondelete='SET NULL',
        ),
        sa.ForeignKeyConstraint(
            ['supplier_account_movement_id'], ['supplier_account_movements.id'], ondelete='SET NULL',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_checks_id'), 'checks', ['id'], unique=False)
    op.create_index(op.f('ix_checks_direction'), 'checks', ['direction'], unique=False)
    op.create_index(op.f('ix_checks_check_number'), 'checks', ['check_number'], unique=False)
    op.create_index(op.f('ix_checks_status'), 'checks', ['status'], unique=False)
    op.create_index(op.f('ix_checks_client_id'), 'checks', ['client_id'], unique=False)
    op.create_index(op.f('ix_checks_supplier_id'), 'checks', ['supplier_id'], unique=False)
    op.create_index(op.f('ix_checks_created_by'), 'checks', ['created_by'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_checks_created_by'), table_name='checks')
    op.drop_index(op.f('ix_checks_supplier_id'), table_name='checks')
    op.drop_index(op.f('ix_checks_client_id'), table_name='checks')
    op.drop_index(op.f('ix_checks_status'), table_name='checks')
    op.drop_index(op.f('ix_checks_check_number'), table_name='checks')
    op.drop_index(op.f('ix_checks_direction'), table_name='checks')
    op.drop_index(op.f('ix_checks_id'), table_name='checks')
    op.drop_table('checks')
