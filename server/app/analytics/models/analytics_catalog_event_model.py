from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, JSON, String, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.product_model import Product
    from app.models.sales_rep_model import SalesRep


class AnalyticsCatalogEvent(Base, TenantMixin):
    __tablename__ = "analytics_catalog_events"
    
    __table_args__ = (
        Index(
            "idx_catalog_event_created_at",
            "created_at",
        ),
        Index(
            "idx_catalog_event_product_created",
            "product_id",
            "created_at",
        ),
        Index(
            "idx_catalog_event_sales_rep_created",
            "sales_rep_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    visitor_id: Mapped[str] = mapped_column(
        String(128),
        index=True,
    )

    session_id: Mapped[str] = mapped_column(
        String(128),
        index=True,
    )
    
    client_id: Mapped[int | None] = mapped_column(
        ForeignKey("clients.id"),
        nullable=True,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(64),
        index=True,
    )

    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id"),
        nullable=True,
        index=True,
    )

    sales_rep_id: Mapped[int | None] = mapped_column(
        ForeignKey("sales_reps.id"),
        nullable=True,
        index=True,
    )

    zone_h3_index: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        index=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    metadata_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    product: Mapped["Product"] = relationship(
        back_populates="catalog_events",
    )

    sales_rep: Mapped["SalesRep"] = relationship(
        back_populates="catalog_events",
    )