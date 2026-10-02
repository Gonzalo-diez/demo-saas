from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.constants.sales_type_constant import SalesType
from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.client_branch_model import ClientBranch
    from app.models.client_model import Client
    from app.models.client_payment_allocation_model import ClientPaymentAllocation
    from app.models.order_model import Order
    from app.models.sales_invoice_item_model import SalesInvoiceItem
    from app.models.sales_invoice_payment_model import SalesInvoicePayment
    from app.models.sales_rep_model import SalesRep


class SalesInvoice(Base, TenantMixin):
    __tablename__ = "sales_invoices"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "invoice_number",
            name="uq_sales_invoice_tenant_number",
        ),
        UniqueConstraint(
            "order_id",
            name="uq_sales_invoice_order_id"
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
        ForeignKey("clients.id"),
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

    customer_name: Mapped[str | None] = mapped_column(
        String(255),
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

    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        index=True,
    )

    # Estado de cobro de ESTE remito puntual (independiente del saldo
    # general de cuenta corriente del cliente). 'pending' | 'partial' | 'paid'
    payment_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )

    # Cuánto se cobró efectivamente de este remito vía asignación de pagos
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    total_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    total_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    margin_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="ARS",
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

    order: Mapped["Order | None"] = relationship(
        "Order",
        back_populates="sales_invoice",
    )

    client: Mapped["Client | None"] = relationship(
        "Client",
        back_populates="sales_invoices",
    )

    client_branch: Mapped["ClientBranch | None"] = relationship(
        "ClientBranch",
        back_populates="sales_invoices",
    )

    payment_allocations: Mapped[list["ClientPaymentAllocation"]] = relationship(
        "ClientPaymentAllocation",
        back_populates="sales_invoice",
    )

    online_payments: Mapped[list["SalesInvoicePayment"]] = relationship(
        "SalesInvoicePayment",
        back_populates="sales_invoice",
    )

    sales_rep: Mapped["SalesRep | None"] = relationship(
        "SalesRep",
        back_populates="sales_invoices",
    )

    items: Mapped[list["SalesInvoiceItem"]] = relationship(
        "SalesInvoiceItem",
        back_populates="sales_invoice",
        cascade="all, delete-orphan",
    )