from __future__ import annotations
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from sqlalchemy import (
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.product_model import Product
    from app.models.sales_invoice_model import SalesInvoice

class SalesInvoiceItem(Base, TenantMixin):
    __tablename__ = "sales_invoice_items"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    sales_invoice_id: Mapped[int] = mapped_column(
        ForeignKey(
            "sales_invoices.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Relación opcional
    # El remito NO debe depender del producto vivo
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id"),
        nullable=True,
        index=True,
    )

    # Snapshot histórico
    product_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    product_brand: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    product_sku: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    # Snapshot completo opcional
    product_snapshot: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    subtotal_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    margin_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    sales_invoice: Mapped["SalesInvoice"] = relationship(
        "SalesInvoice",
        back_populates="items",
    )

    # Relación opcional solo para navegación
    product: Mapped["Product | None"] = relationship(
        "Product",
        back_populates="sales_invoice_items",
        overlaps="sales_invoice_items",
    )