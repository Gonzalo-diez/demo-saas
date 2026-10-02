from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.client_model import Client
    from app.models.order_model import Order
    from app.models.sales_invoice_model import SalesInvoice
    from app.models.sales_quote_model import SalesQuote

class ClientBranch(Base, TenantMixin):
    __tablename__ = "client_branches"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)

    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    h3_index: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)

    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_main: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    client: Mapped["Client"] = relationship("Client", back_populates="branches")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="client_branch")
    sales_invoices: Mapped[list["SalesInvoice"]] = relationship(
        "SalesInvoice",
        back_populates="client_branch",
    )
    sales_quotes: Mapped[list["SalesQuote"]] = relationship(
        "SalesQuote",
        back_populates="client_branch"
    )