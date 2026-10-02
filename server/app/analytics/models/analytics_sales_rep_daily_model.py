from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.sales_rep_model import SalesRep

class AnalyticsSalesRepDaily(Base, TenantMixin):
    __tablename__ = "analytics_sales_rep_daily"

    __table_args__ = (
        UniqueConstraint(
            "date",
            "sales_rep_id",
            name="uq_analytics_sales_rep_daily_date_rep",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    sales_rep_id: Mapped[int] = mapped_column(
        ForeignKey("sales_reps.id"),
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

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    sales_rep: Mapped["SalesRep"] = relationship(
        "SalesRep",
        back_populates="analytics_daily",
    )