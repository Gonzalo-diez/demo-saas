from __future__ import annotations
from typing import TYPE_CHECKING, Any
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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.client_model import Client


class AnalyticsClientDaily(Base, TenantMixin):
    __tablename__ = "analytics_client_daily"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "date",
            "client_id",
            name="uq_analytics_client_daily_tenant_date_client",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id"),
        nullable=False,
        index=True,
    )

    total_orders: Mapped[int] = mapped_column(
        Integer,
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

    # [{product_id, qty, amount, product_name, category, brand}]
    products_bought: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )

    unique_products_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # [{category, qty, amount, unique_products}] — agregado por categoría
    categories_summary: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="analytics_client_daily",
    )