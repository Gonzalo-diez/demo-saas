"""add client email and phone

Revision ID: 39cf238f7e95
Revises: f90a99a4cc7f
Create Date: 2026-08-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39cf238f7e95'
down_revision: Union[str, Sequence[str], None] = 'f90a99a4cc7f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "clients",
        sa.Column("email", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "clients",
        sa.Column("phone", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("clients", "phone")
    op.drop_column("clients", "email")