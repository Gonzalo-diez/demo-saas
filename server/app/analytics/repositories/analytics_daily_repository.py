from __future__ import annotations
from datetime import date
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.analytics.models.analytics_daily_model import AnalyticsDaily
from app.analytics.schemas.analytics_daily_schema import (
    AnalyticsDailyCreate,
)

class AnalyticsDailyRepository:
    def get_by_date(
        self,
        db: Session,
        target_date: date,
    ) -> Optional[AnalyticsDaily]:

        stmt = select(AnalyticsDaily).where(
            AnalyticsDaily.date == target_date
        )

        return db.execute(stmt).scalar_one_or_none()

    def upsert(
        self,
        db: Session,
        obj_in: AnalyticsDailyCreate,
    ) -> AnalyticsDaily:

        existing = self.get_by_date(db, obj_in.date)
        
        if existing:
            existing.total_orders = obj_in.total_orders
            existing.total_clients = obj_in.total_clients
            existing.total_products_sold = obj_in.total_products_sold

            existing.revenue_generated = obj_in.revenue_generated
            existing.cost_generated = obj_in.cost_generated
            existing.margin_generated = obj_in.margin_generated
            existing.average_ticket = obj_in.average_ticket

            db.flush()
            return existing

        db_obj = AnalyticsDaily(
            date=obj_in.date,
            total_orders=obj_in.total_orders,
            total_clients=obj_in.total_clients,
            total_products_sold=obj_in.total_products_sold,
            revenue_generated=obj_in.revenue_generated,
            cost_generated=obj_in.cost_generated,
            margin_generated=obj_in.margin_generated,
            average_ticket=obj_in.average_ticket,
        )

        db.add(db_obj)
        db.flush()

        return db_obj

    def list_range(
        self,
        db: Session,
        *,
        start_date: date,
        end_date: date,
        limit: int = 31,
    ) -> list[AnalyticsDaily]:

        stmt = (
            select(AnalyticsDaily)
            .where(AnalyticsDaily.date >= start_date)
            .where(AnalyticsDaily.date <= end_date)
            .order_by(AnalyticsDaily.date.asc())
            .limit(limit)
        )

        return list(db.execute(stmt).scalars().all())

    def delete_by_date(
        self,
        db: Session,
        target_date: date,
    ) -> None:

        obj = self.get_by_date(db, target_date)

        if obj:
            db.delete(obj)
            db.flush()