from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class TenantMixin:
    """
    Marca a un modelo como "propiedad de un tenant" (una distribuidora).

    El aislamiento NO se hace a mano en cada repository: ver
    app/db/tenant_context.py, que agrega el filtro tenant_id a toda
    lectura/UPDATE/DELETE de modelos con este mixin, y lo completa en
    cada INSERT.
    """

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey(
            "tenants.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
