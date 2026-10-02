from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Boolean, DateTime, func, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from typing import TYPE_CHECKING
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.inventory_movement_model import InventoryMovement
    from app.models.purchase_invoice_item_model import PurchaseInvoiceItem
    from app.models.purchase_quote_item_model import PurchaseQuoteItem
    from app.models.sales_invoice_item_model import SalesInvoiceItem
    from app.models.sales_quote_item_model import SalesQuoteItem
    from app.analytics.models.analytics_zone_product_daily_model import AnalyticsZoneProductDaily
    from app.analytics.models.analytics_product_daily_model import AnalyticsProductDaily
    from app.analytics.models.analytics_catalog_event_model import AnalyticsCatalogEvent

class Product(Base, TenantMixin):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint(
            "unit_price >= 0",
            name="ck_products_price_non_negative",
        ),
        CheckConstraint(
            "stock_current >= 0",
            name="ck_products_stock_non_negative",
        ),
        UniqueConstraint(
            "tenant_id",
            "slug",
            name="uq_products_tenant_slug",
        ),
        UniqueConstraint(
            "tenant_id",
            "sku",
            name="uq_products_tenant_sku",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_normalized: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    brand: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    brand_normalized: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    category_normalized: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="ARS")
    stock_current: Mapped[int] = mapped_column(Integer, default=0)
    stock_min: Mapped[int] = mapped_column(Integer, default=0)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    
    inventory_movements: Mapped[list["InventoryMovement"]] = relationship(
        "InventoryMovement",
        back_populates="product",
    )
    purchase_invoice_items: Mapped[list["PurchaseInvoiceItem"]] = relationship(
        "PurchaseInvoiceItem",
        back_populates="product"
    )
    sales_invoice_items: Mapped[list["SalesInvoiceItem"]] = relationship(
        "SalesInvoiceItem",
        back_populates="product",
    )
    purchase_quote_items: Mapped[list["PurchaseQuoteItem"]] = relationship(
        "PurchaseQuoteItem",
        back_populates="product",
    )
    sales_quote_items: Mapped[list["SalesQuoteItem"]] = relationship(
        "SalesQuoteItem",
        back_populates="product",
    )
    catalog_events: Mapped[list["AnalyticsCatalogEvent"]] = relationship(
        "AnalyticsCatalogEvent",
        back_populates="product",
    )
    analytics_daily: Mapped[list["AnalyticsProductDaily"]] = relationship(
        "AnalyticsProductDaily",
        back_populates="product",
        lazy="select",
        viewonly=True
    )
    analytics_zone_daily: Mapped[list["AnalyticsZoneProductDaily"]] = relationship(
        "AnalyticsZoneProductDaily",
        back_populates="product",
        lazy="select",
        viewonly=True
    )