from __future__ import annotations
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.product_model import Product
    from app.models.purchase_invoice_model import PurchaseInvoice

class PurchaseInvoiceItem(Base, TenantMixin):
    __tablename__ = "purchase_invoice_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    purchase_invoice_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id"),
        nullable=True,
        index=True,
    )

    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    purchase_invoice: Mapped["PurchaseInvoice"] = relationship(
        "PurchaseInvoice",
        back_populates="items",
    )
    product: Mapped["Product | None"] = relationship("Product", back_populates="purchase_invoice_items", overlaps="purchase_invoice_items")