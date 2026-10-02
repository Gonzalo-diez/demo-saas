"""add_notifications

Revision ID: b3f6a1c8d2e5
Revises: 6f05112e6791
Create Date: 2026-09-30 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b3f6a1c8d2e5'
down_revision: Union[str, None] = '6f05112e6791'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=20), nullable=False),
        sa.Column('type', sa.String(length=40), nullable=False),
        sa.Column('severity', sa.String(length=10), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('dedup_key', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=20), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('notified_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_category'), 'notifications', ['category'], unique=False)
    op.create_index(op.f('ix_notifications_type'), 'notifications', ['type'], unique=False)
    op.create_index(op.f('ix_notifications_resolved_at'), 'notifications', ['resolved_at'], unique=False)
    op.create_index('ix_notifications_entity', 'notifications', ['entity_type', 'entity_id'], unique=False)
    op.create_index(
        'uq_notifications_active_dedup_key',
        'notifications',
        ['dedup_key'],
        unique=True,
        postgresql_where=sa.text('resolved_at IS NULL'),
    )

    op.create_table(
        'notification_reads',
        sa.Column('notification_id', sa.Integer(), nullable=False),
        sa.Column('sales_rep_id', sa.Integer(), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['notification_id'], ['notifications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sales_rep_id'], ['sales_reps.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('notification_id', 'sales_rep_id'),
    )
    op.create_index(op.f('ix_notification_reads_sales_rep_id'), 'notification_reads', ['sales_rep_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_notification_reads_sales_rep_id'), table_name='notification_reads')
    op.drop_table('notification_reads')
    op.drop_index('uq_notifications_active_dedup_key', table_name='notifications', postgresql_where=sa.text('resolved_at IS NULL'))
    op.drop_index('ix_notifications_entity', table_name='notifications')
    op.drop_index(op.f('ix_notifications_resolved_at'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_type'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_category'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
