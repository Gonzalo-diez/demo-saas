from __future__ import annotations
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.product_model import Product
    from app.models.purchase_quote_model import PurchaseQuote


class PurchaseQuoteItem(Base, TenantMixin):
    __tablename__ = "purchase_quote_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    purchase_quote_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_quotes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_sku: Mapped[str | None] = mapped_column(String(120), nullable=True)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    purchase_quote: Mapped["PurchaseQuote"] = relationship(
        "PurchaseQuote",
        back_populates="items",
    )
    product: Mapped["Product | None"] = relationship(
        "Product",
        back_populates="purchase_quote_items",
    )