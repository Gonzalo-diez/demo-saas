from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.supplier_account_movement_model import SupplierAccountMovement
    from app.models.purchase_invoice_model import PurchaseInvoice
    from app.models.purchase_quote_model import PurchaseQuote

class SupplierPaymentAllocation(Base, TenantMixin):
    """
    Registra cuánto de un pago (SupplierAccountMovement de tipo 'payment')
    se imputó a un documento de compra puntual: un remito de compra
    (PurchaseInvoice) o un presupuesto de compra (PurchaseQuote). Un mismo
    pago puede repartirse entre varios documentos (o ninguno, si se paga
    'a cuenta').

    Cada fila apunta a EXACTAMENTE uno de los dos documentos
    (ver ck_supplier_payment_allocation_one_document).
    """
    __tablename__ = "supplier_payment_allocations"

    __table_args__ = (
        CheckConstraint(
            "(purchase_invoice_id IS NOT NULL AND purchase_quote_id IS NULL) "
            "OR (purchase_invoice_id IS NULL AND purchase_quote_id IS NOT NULL)",
            name="ck_supplier_payment_allocation_one_document",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    supplier_account_movement_id: Mapped[int] = mapped_column(
        ForeignKey("supplier_account_movements.id"),
        nullable=False,
        index=True,
    )

    purchase_invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("purchase_invoices.id"),
        nullable=True,
        index=True,
    )

    purchase_quote_id: Mapped[int | None] = mapped_column(
        ForeignKey("purchase_quotes.id"),
        nullable=True,
        index=True,
    )

    amount_applied: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    movement: Mapped["SupplierAccountMovement"] = relationship(
        "SupplierAccountMovement",
        back_populates="allocations",
    )
    purchase_invoice: Mapped["PurchaseInvoice | None"] = relationship(
        "PurchaseInvoice",
        back_populates="payment_allocations",
    )
    purchase_quote: Mapped["PurchaseQuote | None"] = relationship(
        "PurchaseQuote",
        back_populates="payment_allocations",
    )
