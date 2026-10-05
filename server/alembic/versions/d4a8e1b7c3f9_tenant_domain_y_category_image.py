"""dominio de la tienda por tenant + imagen de categoría

Revision ID: d4a8e1b7c3f9
Revises: c0ffee5a1d01
Create Date: 2026-10-03 12:00:00

- tenants.domain: host con el que los clientes entran a la tienda de la distribuidora
  (único, obligatorio). Las distribuidoras que ya existían reciben "<slug>.localhost"
  (que en desarrollo resuelve a 127.0.0.1); hay que cambiarlo por el dominio real
  desde el panel de plataforma (PATCH /api/tenants/{id}).
- categories.image_url: imagen de la categoría. Obligatoria para publicarla (lo valida
  el service), por eso la columna es nullable: las privadas pueden no tenerla.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4a8e1b7c3f9"
down_revision: Union[str, None] = "c0ffee5a1d01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("categories", sa.Column("image_url", sa.String(), nullable=True))

    op.add_column("tenants", sa.Column("domain", sa.String(length=255), nullable=True))
    op.execute("UPDATE tenants SET domain = slug || '.localhost' WHERE domain IS NULL")
    op.alter_column("tenants", "domain", existing_type=sa.String(length=255), nullable=False)
    op.create_index(op.f("ix_tenants_domain"), "tenants", ["domain"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_tenants_domain"), table_name="tenants")
    op.drop_column("tenants", "domain")
    op.drop_column("categories", "image_url")
