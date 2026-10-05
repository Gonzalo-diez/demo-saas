from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.product_model import Product
    from app.models.sales_rep_model import SalesRep


class ProductPurchase(Base, TenantMixin):
    """
    Historial de compras de un producto: cada ingreso de mercadería queda registrado con
    su cantidad, su costo, el precio de venta que se fijó en ese momento y su vencimiento.

    Es un REGISTRO (no se edita ni se borra): `products.unit_cost` es el costo promedio
    ponderado actual y acá queda la foto de cada compra, para ver cómo fue cambiando el
    costo y el precio.

    source: "initial_stock" (alta del producto) · "manual" (compra cargada a mano) ·
            "purchase_invoice" (remito de compra) · "import" (importación Excel)
    """

    __tablename__ = "product_purchases"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_product_purchases_quantity_positive"),
        CheckConstraint("unit_cost >= 0", name="ck_product_purchases_cost_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False, index=True
    )

    purchase_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # % de remarque sobre el costo con el que se calculó el precio (si se usó) y el precio de
    # venta fijado en esa compra. Pueden ser null (ej. remitos: no fijan precio).
    markup_percent: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    sale_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    source: Mapped[str] = mapped_column(String(30), nullable=False, default="manual")
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("sales_reps.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    product: Mapped["Product"] = relationship("Product")
    creator: Mapped["SalesRep | None"] = relationship("SalesRep")
