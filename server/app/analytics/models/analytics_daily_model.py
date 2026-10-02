from __future__ import annotations
from datetime import date, datetime
from typing import TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import (
    Date,
    DateTime,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

from app.models.mixin_model import TenantMixin

class AnalyticsDaily(Base, TenantMixin):
    __tablename__ = "analytics_daily"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "date",
            name="uq_analytics_daily_tenant_date",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    total_orders: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    total_clients: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    total_products_sold: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
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

    average_ticket: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )