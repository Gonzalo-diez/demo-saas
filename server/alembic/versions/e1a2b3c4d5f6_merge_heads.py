"""merge heads (sales_invoice_payments, account_movements, online_customer)

Revision ID: e1a2b3c4d5f6
Revises: d5e3a7c1f9b2, b7a1c9f3e2d4, 60cecc3cdbd8
Create Date: 2026-08-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1a2b3c4d5f6'
down_revision: Union[str, tuple[str, ...], None] = (
    'd5e3a7c1f9b2',
    'b7a1c9f3e2d4',
    '60cecc3cdbd8',
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Migración de fusión: no cambia el esquema, solo une las 3 ramas
    # que habían quedado separadas en el árbol de Alembic.
    pass


def downgrade() -> None:
    pass