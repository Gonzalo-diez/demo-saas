from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixin_model import TenantMixin


class Category(Base, TenantMixin):
    """
    Categoría de productos de UNA distribuidora (tenant). Cada distribuidora
    crea las suyas; no hay una lista fija en el código.

    - is_public: si es False, los productos de esta categoría no aparecen en el
      catálogo que ven los clientes (siguen disponibles para venta B2B interna).
      Para ser pública necesita image_url.
    - requires_age_verification: los pedidos online con productos de esta
      categoría exigen DNI + declaración de mayoría de edad (ej. tabaco,
      Ley 26.687). Antes estaba fijo en el código para 3 categorías.
    """

    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name_normalized", name="uq_categories_tenant_name"),
        UniqueConstraint("tenant_id", "slug", name="uq_categories_tenant_slug"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_normalized: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Imagen de la categoría (la tienda la muestra como portada). Igual que en
    # Product: es obligatoria para que la categoría se vea en el catálogo
    # (is_public=True); una categoría privada puede no tenerla.
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)

    is_public: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    requires_age_verification: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
