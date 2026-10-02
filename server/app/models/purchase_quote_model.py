from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.purchase_quote_item_model import PurchaseQuoteItem
    from app.models.sales_rep_model import SalesRep
    from app.models.supplier_model import Supplier
    from app.models.supplier_payment_allocation_model import SupplierPaymentAllocation

class PurchaseQuote(Base, TenantMixin):
    """
    Presupuesto de compra: cotización de productos a un proveedor,
    independiente de los remitos de compra (PurchaseInvoice). No genera
    movimientos de stock ni de cuenta corriente; es solo para cotizar.
    """

    __tablename__ = "purchase_quotes"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "quote_number",
            name="uq_purchase_quote_tenant_number",
        ),
        CheckConstraint(
            "status IN ('draft', 'sent', 'approved', 'rejected', 'expired')",
            name="ck_purchase_quote_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    supplier_tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    supplier_snapshot: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    quote_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    quote_date: Mapped[date] = mapped_column(Date, nullable=False)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", server_default="draft", index=True)

    payment_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )
    
    # Igual que PurchaseInvoice: NOT NULL con default 0 para poder hacer
    # `total - paid_amount` sin chequear None.
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    total_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("sales_reps.id"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    items: Mapped[list["PurchaseQuoteItem"]] = relationship(
        "PurchaseQuoteItem",
        back_populates="purchase_quote",
        cascade="all, delete-orphan",
    )
    creator: Mapped["SalesRep | None"] = relationship(
        "SalesRep",
        back_populates="purchase_quotes",
    )
    supplier: Mapped["Supplier | None"] = relationship("Supplier", back_populates="purchase_quotes")
    payment_allocations: Mapped[list["SupplierPaymentAllocation"]] = relationship(
        "SupplierPaymentAllocation",
        back_populates="purchase_quote",
    )