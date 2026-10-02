"""add email_last_sent_at and remove whatsapp fields

Revision ID: e0005eb204da
Revises: 39f17ff2f91c
Create Date: 2026-04-08 12:39:48.708049

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e0005eb204da"
down_revision: Union[str, None] = "39f17ff2f91c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("email_last_sent_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.drop_column("orders", "whatsapp_confirmation_requested_at")
    op.drop_column("orders", "whatsapp_last_sent_at")
    op.drop_column("orders", "whatsapp_last_message_id")
    op.drop_column("orders", "whatsapp_confirmed_at")


def downgrade() -> None:
    op.add_column(
        "orders",
        sa.Column(
            "whatsapp_confirmed_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "whatsapp_last_message_id",
            sa.VARCHAR(length=255),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "whatsapp_last_sent_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "whatsapp_confirmation_requested_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
    )

    op.drop_column("orders", "email_last_sent_at")