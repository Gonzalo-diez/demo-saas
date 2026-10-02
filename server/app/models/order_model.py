from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.constants.sales_type_constant import SalesType
from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.client_branch_model import ClientBranch
    from app.models.client_model import Client
    from app.models.order_item_model import OrderItem
    from app.models.sales_invoice_model import SalesInvoice
    from app.models.sales_quote_model import SalesQuote
    from app.models.sales_rep_model import SalesRep


class Order(Base, TenantMixin):
    __tablename__ = "orders"

    __table_args__ = (
        CheckConstraint(
            "total_amount >= 0",
            name="ck_orders_total_non_negative",
        ),
        CheckConstraint(
            """
            (
                sales_type = 'B2B'
                AND sales_rep_id IS NOT NULL
            )
            OR
            (
                sales_type = 'ONLINE'
                AND sales_rep_id IS NULL
            )
            """,
            name="ck_order_sales_rep_validation",
        ),
        CheckConstraint(
            """
            (
                sales_type = 'ONLINE'
                AND customer_name IS NOT NULL
                AND customer_email IS NOT NULL
                AND customer_phone IS NOT NULL
                AND delivery_type IS NOT NULL
                AND delivery_address IS NOT NULL
                AND delivery_city IS NOT NULL
                AND preferred_delivery_date IS NOT NULL
            )
            OR
            (
                sales_type = 'B2B'
                AND client_id IS NOT NULL
            )
            """,
            name="ck_sales_type_validation",
        ),
        CheckConstraint(
            """
            scheduled_delivery_date IS NULL
            OR preferred_delivery_date IS NULL
            OR scheduled_delivery_date >= preferred_delivery_date
            """,
            name="ck_order_delivery_dates_validation"
        ),
        CheckConstraint(
            "document_type IN ('sales_invoice', 'sales_quote')",
            name="ck_order_document_type",
        ),
        Index(
            "ix_orders_scheduled_delivery_status",
            "scheduled_delivery_date",
            "status",
        ),
        Index(
            "ix_orders_sales_rep_delivery_date",
            "sales_rep_id",
            "scheduled_delivery_date",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    sales_type: Mapped[str] = mapped_column(
        Enum(SalesType, name="sales_type_enum"),
        nullable=False,
        server_default=SalesType.ONLINE.value,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending_confirmation",
        index=True,
    )

    # Documento de venta que se genera cuando el pedido pasa a 'preparing':
    # 'sales_invoice' (remito de venta) o 'sales_quote' (presupuesto de venta).
    # Lo elige el comprador en el checkout (o el vendedor en un pedido B2B).
    document_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="sales_invoice",
        server_default="sales_invoice",
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

    # --- Verificación de identidad / cumplimiento normativo ---
    # DNI y declaración de mayoría de edad: obligatorios en el checkout
    # cuando el pedido incluye productos regulados (tabaco), según
    # Ley 26.687. Quedan guardados como constancia de la declaración.
    customer_dni: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    age_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # --- Datos fiscales declarados en el checkout ---
    customer_tax_id: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
    )
    customer_person_type: Mapped[str | None] = mapped_column(
        String(20),  # "individual" | "empresa"
        nullable=True,
    )
    customer_iva_condition: Mapped[str | None] = mapped_column(
        String(30),  # consumidor_final | responsable_inscripto | monotributista | exento
        nullable=True,
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

    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    margin_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="ARS",
    )

    stock_consumed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    
    preferred_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )
    
    scheduled_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )
    
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    invoice_generated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    email_last_sent_at: Mapped[datetime | None] = mapped_column(
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

    client: Mapped["Client | None"] = relationship(
        "Client",
        back_populates="orders",
    )

    client_branch: Mapped["ClientBranch | None"] = relationship(
        "ClientBranch",
        back_populates="orders",
    )

    sales_rep: Mapped["SalesRep | None"] = relationship(
        "SalesRep",
        back_populates="orders",
    )

    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    sales_invoice: Mapped["SalesInvoice | None"] = relationship(
        "SalesInvoice",
        back_populates="order",
        uselist=False,
    )
    
    sales_quote: Mapped["SalesQuote | None"] = relationship(
        "SalesQuote",
        back_populates="order",
        uselist=False,
    )