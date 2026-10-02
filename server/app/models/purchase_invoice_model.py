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
    from app.models.purchase_invoice_item_model import PurchaseInvoiceItem
    from app.models.sales_rep_model import SalesRep
    from app.models.supplier_model import Supplier
    from app.models.supplier_payment_allocation_model import SupplierPaymentAllocation

class PurchaseInvoice(Base, TenantMixin):
    __tablename__ = "purchase_invoices"
    
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "invoice_number", 
            name="uq_purchase_invoice_tenant_number"
        ),
        CheckConstraint(
            "status IN ('draft', 'confirmed', 'cancelled')",
            name="ck_purchase_invoice_status",
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
    
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)

    # Estado de pago de ESTE remito puntual (independiente del saldo
    # general de cuenta corriente del proveedor). 'pending' | 'partial' | 'paid'
    payment_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )

    # Cuánto se pagó efectivamente de este remito vía asignación de pagos
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

    items: Mapped[list["PurchaseInvoiceItem"]] = relationship(
        "PurchaseInvoiceItem",
        back_populates="purchase_invoice",
        cascade="all, delete-orphan",
    )
    creator: Mapped["SalesRep | None"] = relationship(
        "SalesRep",
        back_populates="purchase_invoices",
    )
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="purchase_invoices")
    payment_allocations: Mapped[list["SupplierPaymentAllocation"]] = relationship(
        "SupplierPaymentAllocation",
        back_populates="purchase_invoice",
    )