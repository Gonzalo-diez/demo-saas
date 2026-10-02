from __future__ import annotations
from datetime import datetime
from typing import Sequence, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from app.analytics.models.analytics_catalog_event_model import AnalyticsCatalogEvent
from app.analytics.schemas.analytics_catalog_event_schema import (
    AnalyticsCatalogEventCreate,
)

class AnalyticsCatalogEventRepository:
    def create(
        self,
        db: Session,
        obj_in: AnalyticsCatalogEventCreate,
    ) -> AnalyticsCatalogEvent:

        db_obj = AnalyticsCatalogEvent(
            visitor_id=obj_in.visitor_id,
            session_id=obj_in.session_id,
            event_type=obj_in.event_type,
            product_id=obj_in.product_id,
            sales_rep_id=obj_in.sales_rep_id,
            zone_h3_index=obj_in.zone_h3_index,
            source=obj_in.source,
            metadata_json=obj_in.metadata_json,
        )

        db.add(db_obj)
        db.flush()  # importante para obtener ID sin commit
        return db_obj

    def bulk_create(
        self,
        db: Session,
        objs_in: list[AnalyticsCatalogEventCreate],
    ) -> None:

        db.bulk_save_objects([
            AnalyticsCatalogEvent(
                visitor_id=obj.visitor_id,
                session_id=obj.session_id,
                event_type=obj.event_type,
                product_id=obj.product_id,
                sales_rep_id=obj.sales_rep_id,
                zone_h3_index=obj.zone_h3_index,
                source=obj.source,
                metadata_json=obj.metadata_json,
            )
            for obj in objs_in
        ])

    def get_by_id(
        self,
        db: Session,
        event_id: int,
    ) -> Optional[AnalyticsCatalogEvent]:

        return db.get(AnalyticsCatalogEvent, event_id)

    def list_events(
        self,
        db: Session,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        event_type: str | None = None,
        product_id: int | None = None,
        sales_rep_id: int | None = None,
        visitor_id: str | None = None,
        session_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AnalyticsCatalogEvent]:

        stmt = select(AnalyticsCatalogEvent)

        filters = []

        if start_date:
            filters.append(AnalyticsCatalogEvent.created_at >= start_date)

        if end_date:
            filters.append(AnalyticsCatalogEvent.created_at <= end_date)

        if event_type:
            filters.append(AnalyticsCatalogEvent.event_type == event_type)

        if product_id:
            filters.append(AnalyticsCatalogEvent.product_id == product_id)

        if sales_rep_id:
            filters.append(AnalyticsCatalogEvent.sales_rep_id == sales_rep_id)

        if visitor_id:
            filters.append(AnalyticsCatalogEvent.visitor_id == visitor_id)

        if session_id:
            filters.append(AnalyticsCatalogEvent.session_id == session_id)

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(AnalyticsCatalogEvent.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)

        return list(db.execute(stmt).scalars().all())

    def count_events(
        self,
        db: Session,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        event_type: str | None = None,
        product_id: int | None = None,
    ) -> int:

        stmt = select(func.count(AnalyticsCatalogEvent.id))

        filters = []

        if start_date:
            filters.append(AnalyticsCatalogEvent.created_at >= start_date)

        if end_date:
            filters.append(AnalyticsCatalogEvent.created_at <= end_date)

        if event_type:
            filters.append(AnalyticsCatalogEvent.event_type == event_type)

        if product_id:
            filters.append(AnalyticsCatalogEvent.product_id == product_id)

        if filters:
            stmt = stmt.where(and_(*filters))

        return db.execute(stmt).scalar_one()