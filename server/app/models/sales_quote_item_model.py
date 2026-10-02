from __future__ import annotations
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.product_model import Product
    from app.models.sales_quote_model import SalesQuote

class SalesQuoteItem(Base, TenantMixin):
    __tablename__ = "sales_quote_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    sales_quote_id: Mapped[int] = mapped_column(
        ForeignKey("sales_quotes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_sku: Mapped[str | None] = mapped_column(String(120), nullable=True)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    # Costos: nullable porque un presupuesto suelto (importado de PDF o
    # cargado a mano sin producto vinculado) no conoce el costo. En un
    # presupuesto que nace de un pedido siempre vienen completos.
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    subtotal_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    margin_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    sales_quote: Mapped["SalesQuote"] = relationship(
        "SalesQuote",
        back_populates="items",
    )
    product: Mapped["Product | None"] = relationship(
        "Product",
        back_populates="sales_quote_items",
    )