from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.sales_invoice_model import SalesInvoice
    from app.models.sales_rep_model import SalesRep

class SalesInvoicePayment(Base, TenantMixin):
    """
    Registro simple de cobro de un remito de venta puntual (típicamente
    ONLINE, cobrada contra entrega — efectivo, Mercado Pago, transferencia).

    A diferencia de ClientAccountMovement, esto NO implica una cuenta
    corriente ni un saldo que se acumula entre remitos: es solo un
    historial de "cuánto y cómo se cobró" para ESTE remito puntual.
    """
    __tablename__ = "sales_invoice_payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    sales_invoice_id: Mapped[int] = mapped_column(
        ForeignKey("sales_invoices.id"),
        nullable=False,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)
    # 'efectivo' | 'debito' | 'credito' | 'cheque' | 'otro'

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

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

    sales_invoice: Mapped["SalesInvoice"] = relationship(
        "SalesInvoice",
        back_populates="online_payments",
    )
    creator: Mapped["SalesRep | None"] = relationship("SalesRep")