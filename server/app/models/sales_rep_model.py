from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, Float, String, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.client_model import Client
    from app.models.client_account_movement_model import ClientAccountMovement
    from app.models.inventory_movement_model import InventoryMovement
    from app.models.order_model import Order
    from app.models.purchase_invoice_model import PurchaseInvoice
    from app.models.purchase_quote_model import PurchaseQuote
    from app.models.sales_invoice_model import SalesInvoice
    from app.models.sales_quote_model import SalesQuote
    from app.models.supplier_account_movement_model import SupplierAccountMovement
    from app.analytics.models.analytics_sales_rep_daily_model import AnalyticsSalesRepDaily
    from app.analytics.models.analytics_catalog_event_model import AnalyticsCatalogEvent

class SalesRep(Base, TenantMixin):
    __tablename__ = "sales_reps"
    
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "email",
            name="uq_sales_reps_tenant_email",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    home_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    home_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    coverage_radius_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    home_h3_index: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    clients: Mapped[list["Client"]] = relationship("Client", back_populates="sales_rep")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="sales_rep")
    purchase_invoices: Mapped[list["PurchaseInvoice"]] = relationship(
        "PurchaseInvoice",
        back_populates="creator",
    )
    purchase_quotes: Mapped[list["PurchaseQuote"]] = relationship(
        "PurchaseQuote",
        back_populates="creator",
    )
    sales_quotes: Mapped[list["SalesQuote"]] = relationship(
        "SalesQuote",
        back_populates="sales_rep",
    )
    inventory_movements: Mapped[list["InventoryMovement"]] = relationship(
        "InventoryMovement",
        back_populates="creator",
    )
    sales_invoices: Mapped[list["SalesInvoice"]] = relationship(
        "SalesInvoice",
        back_populates="sales_rep",
    )
    catalog_events: Mapped[list["AnalyticsCatalogEvent"]] = relationship(
        "AnalyticsCatalogEvent",
        back_populates="sales_rep",
    )
    analytics_daily: Mapped[list["AnalyticsSalesRepDaily"]] = relationship(
        "AnalyticsSalesRepDaily",
        back_populates="sales_rep",
        lazy="select",
        viewonly=True,
    )
    client_account_movements: Mapped[list["ClientAccountMovement"]] = relationship(
        "ClientAccountMovement",
        back_populates="creator",
    )
    supplier_account_movements: Mapped[list["SupplierAccountMovement"]] = relationship(
        "SupplierAccountMovement",
        back_populates="creator",
    )