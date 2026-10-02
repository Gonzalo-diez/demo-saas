from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.product_model import Product

class AnalyticsProductDaily(Base, TenantMixin):
    __tablename__ = "analytics_product_daily"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "date",
            "product_id",
            name="uq_analytics_product_daily_tenant_date_product",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    quantity_sold: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
    
    total_orders: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )
    
    unique_clients: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )

    revenue_generated: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    cost_generated: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    margin_generated: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="analytics_daily",
    )