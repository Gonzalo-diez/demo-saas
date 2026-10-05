"""merge admin y categorias

Une las dos ramas que salían de 53d678be9feb:
  - 7c1d9e4a52b8 (categorías por distribuidora + publicación)
  - fcc5d18c6c2e (tabla admins de plataforma, vía b125fdedce38)

Revision ID: c0ffee5a1d01
Revises: 7c1d9e4a52b8, fcc5d18c6c2e
Create Date: 2026-10-02 21:00:00

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "c0ffee5a1d01"
down_revision: Union[str, Sequence[str], None] = ("7c1d9e4a52b8", "fcc5d18c6c2e")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
