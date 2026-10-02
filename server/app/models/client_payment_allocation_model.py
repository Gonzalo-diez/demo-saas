from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.client_account_movement_model import ClientAccountMovement
    from app.models.sales_invoice_model import SalesInvoice
    from app.models.sales_quote_model import SalesQuote

class ClientPaymentAllocation(Base, TenantMixin):
    """
    Registra cuánto de un cobro (ClientAccountMovement de tipo 'payment')
    se imputó a un documento de venta puntual: un remito (SalesInvoice) o
    un presupuesto de venta que nació de un pedido (SalesQuote). Un mismo
    cobro puede repartirse entre varios documentos (o ninguno, si el
    cliente paga 'a cuenta' sin especificar contra qué documento).

    Cada fila apunta a EXACTAMENTE uno de los dos documentos
    (ver ck_client_payment_allocation_one_document).
    """
    __tablename__ = "client_payment_allocations"

    __table_args__ = (
        CheckConstraint(
            "(sales_invoice_id IS NOT NULL AND sales_quote_id IS NULL) "
            "OR (sales_invoice_id IS NULL AND sales_quote_id IS NOT NULL)",
            name="ck_client_payment_allocation_one_document",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    client_account_movement_id: Mapped[int] = mapped_column(
        ForeignKey("client_account_movements.id"),
        nullable=False,
        index=True,
    )

    sales_invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("sales_invoices.id"),
        nullable=True,
        index=True,
    )

    sales_quote_id: Mapped[int | None] = mapped_column(
        ForeignKey("sales_quotes.id"),
        nullable=True,
        index=True,
    )

    amount_applied: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    movement: Mapped["ClientAccountMovement"] = relationship(
        "ClientAccountMovement",
        back_populates="allocations",
    )
    sales_invoice: Mapped["SalesInvoice | None"] = relationship(
        "SalesInvoice",
        back_populates="payment_allocations",
    )
    sales_quote: Mapped["SalesQuote | None"] = relationship(
        "SalesQuote",
        back_populates="payment_allocations",
    )
