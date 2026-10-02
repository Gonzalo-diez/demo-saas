from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from sqlalchemy import Enum, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.constants.sales_type_constant import SalesType
from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.client_model import Client
    from app.models.client_branch_model import ClientBranch
    from app.models.client_payment_allocation_model import ClientPaymentAllocation
    from app.models.sales_quote_payment_model import SalesQuotePayment
    from app.models.sales_quote_item_model import SalesQuoteItem
    from app.models.order_model import Order
    from app.models.sales_rep_model import SalesRep


class SalesQuote(Base, TenantMixin):
    """
    Presupuesto de venta. Tiene dos usos que conviven en la misma tabla y
    se distinguen por `order_id`:

    1) Cotización suelta (order_id NULL): la carga un vendedor a mano o se
       importa desde un PDF. No genera movimientos de stock ni de cuenta
       corriente; es solo para cotizar (draft/sent/approved/rejected/expired).

    2) Documento de venta de un pedido (order_id NOT NULL): es el "remito
       alternativo" que se genera cuando el pedido (Order) elige
       document_type='sales_quote' y pasa a 'preparing'. Nace 'approved',
       registra la deuda en la cuenta corriente del cliente (igual que un
       SalesInvoice confirmado) y admite cobros imputados
       (ClientPaymentAllocation.sales_quote_id). El stock lo maneja el
       pedido, no el presupuesto.
    """

    __tablename__ = "sales_quotes"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "quote_number",
            name="uq_sales_quote_tenant_number",
        ),
        UniqueConstraint(
            "order_id",
            name="uq_sales_quote_order_id"
        ),
        CheckConstraint(
            "status IN ('draft', 'sent', 'approved', 'rejected', 'expired', 'cancelled')",
            name="ck_sales_quote_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("orders.id"),
        nullable=True,
        index=True,
    )

    sales_type: Mapped[str] = mapped_column(
        Enum(SalesType, name="sales_type_enum"),
        nullable=False,
        index=True,
    )

    client_id: Mapped[int | None] = mapped_column(
        ForeignKey("clients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    client_branch_id: Mapped[int | None] = mapped_column(
        ForeignKey("client_branches.id"),
        nullable=True,
        index=True,
    )

    sales_rep_id: Mapped[int | None] = mapped_column(
        ForeignKey("sales_reps.id"),
        nullable=True,
        index=True,
    )

    # Datos del comprador. Para un cliente registrado se copian del cliente/
    # pedido; para "consumidor final" (sin client_id) son el dato libre.
    customer_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    customer_tax_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    customer_phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    customer_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    delivery_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    delivery_address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    delivery_city: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    delivery_reference: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    client_snapshot: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    client_branch_snapshot: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    sales_rep_snapshot: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    quote_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    quote_date: Mapped[date] = mapped_column(Date, nullable=False)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", server_default="draft", index=True)

    # Forma de pago acordada / impresa en el presupuesto (EFECTIVO,
    # TRANSFERENCIA, ...). Es un dato descriptivo: los cobros reales se
    # registran como ClientAccountMovement + ClientPaymentAllocation.
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Estado de cobro de ESTE presupuesto (solo relevante si order_id no es
    # NULL): 'pending' | 'partial' | 'paid'
    payment_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )

    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    total_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    total_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    margin_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="ARS",
        server_default="ARS",
    )

    pdf_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    email_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    # Order.sales_quote (uselist=False) es el lado inverso: 1 pedido -> 0..1 presupuesto.
    order: Mapped["Order | None"] = relationship(
        "Order",
        back_populates="sales_quote",
    )
    items: Mapped[list["SalesQuoteItem"]] = relationship(
        "SalesQuoteItem",
        back_populates="sales_quote",
        cascade="all, delete-orphan",
    )
    client: Mapped["Client | None"] = relationship("Client", back_populates="sales_quotes")
    client_branch: Mapped["ClientBranch | None"] = relationship(
        "ClientBranch",
        back_populates="sales_quotes",
    )
    sales_rep: Mapped["SalesRep | None"] = relationship(
        "SalesRep",
        back_populates="sales_quotes",
    )
    payment_allocations: Mapped[list["ClientPaymentAllocation"]] = relationship(
        "ClientPaymentAllocation",
        back_populates="sales_quote",
    )
    online_payments: Mapped[list["SalesQuotePayment"]] = relationship(
        "SalesQuotePayment",
        back_populates="sales_quote"
    )