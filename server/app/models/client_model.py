from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.client_branch_model import ClientBranch
    from app.models.client_account_movement_model import ClientAccountMovement
    from app.models.order_model import Order
    from app.models.sales_invoice_model import SalesInvoice
    from app.models.sales_quote_model import SalesQuote
    from app.models.sales_rep_model import SalesRep
    from app.analytics.models.analytics_client_daily_model import AnalyticsClientDaily

class Client(Base, TenantMixin):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    client_type: Mapped[str] = mapped_column(String(50), nullable=False)
    tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    sales_rep_id: Mapped[int | None] = mapped_column(
        ForeignKey("sales_reps.id"),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Saldo cacheado de cuenta corriente (positivo = el cliente nos debe).
    # Fuente de verdad real es el ledger en ClientAccountMovement; este campo
    # se mantiene sincronizado en la misma transacción para lecturas rápidas.
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
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

    sales_rep: Mapped["SalesRep | None"] = relationship(
        "SalesRep",
        back_populates="clients",
    )
    orders: Mapped[list["Order"]] = relationship(
        "Order",
        back_populates="client",
    )
    branches: Mapped[list["ClientBranch"]] = relationship(
        "ClientBranch",
        back_populates="client",
        cascade="all, delete-orphan",
    )
    sales_invoices: Mapped[list["SalesInvoice"]] = relationship(
        "SalesInvoice",
        back_populates="client",
    )
    analytics_client_daily: Mapped[list["AnalyticsClientDaily"]] = relationship(
        "AnalyticsClientDaily",
        back_populates="client",
        lazy="select",
        viewonly=True,
    )
    account_movements: Mapped[list["ClientAccountMovement"]] = relationship(
        "ClientAccountMovement",
        back_populates="client",
    )
    sales_quotes: Mapped[list["SalesQuote"]] = relationship(
        "SalesQuote",
        back_populates="client",
    )