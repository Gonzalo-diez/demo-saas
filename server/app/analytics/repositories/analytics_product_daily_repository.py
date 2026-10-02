from __future__ import annotations
from datetime import date
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.analytics.models.analytics_product_daily_model import AnalyticsProductDaily
from app.analytics.schemas.analytics_product_daily_schema import (
    AnalyticsProductDailyCreate,
)

class AnalyticsProductDailyRepository:
    def get_by_date_and_product(
        self,
        db: Session,
        target_date: date,
        product_id: int,
    ) -> Optional[AnalyticsProductDaily]:

        stmt = select(AnalyticsProductDaily).where(
            AnalyticsProductDaily.date == target_date,
            AnalyticsProductDaily.product_id == product_id,
        )

        return db.execute(stmt).scalar_one_or_none()

    def upsert(
        self,
        db: Session,
        obj_in: AnalyticsProductDailyCreate,
    ) -> AnalyticsProductDaily:

        existing = self.get_by_date_and_product(
            db,
            obj_in.date,
            obj_in.product_id,
        )

        if existing:
            existing.quantity_sold = obj_in.quantity_sold
            existing.total_orders = obj_in.total_orders
            existing.unique_clients = obj_in.unique_clients
            existing.revenue_generated = obj_in.revenue_generated
            existing.cost_generated = obj_in.cost_generated
            existing.margin_generated = obj_in.margin_generated

            db.flush()
            return existing

        db_obj = AnalyticsProductDaily(
            date=obj_in.date,
            product_id=obj_in.product_id,
            quantity_sold=obj_in.quantity_sold,
            total_orders=obj_in.total_orders,
            unique_clients=obj_in.unique_clients,
            revenue_generated=obj_in.revenue_generated,
            cost_generated=obj_in.cost_generated,
            margin_generated=obj_in.margin_generated,
        )

        db.add(db_obj)
        db.flush()

        return db_obj
    
    def bulk_upsert(
        self,
        db: Session,
        items: list[AnalyticsProductDailyCreate],
    ) -> None:

        for item in items:
            existing = self.get_by_date_and_product(
                db,
                item.date,
                item.product_id,
            )

            if existing:
                existing.quantity_sold = item.quantity_sold
                existing.total_orders = item.total_orders
                existing.unique_clients = item.unique_clients
                existing.revenue_generated = item.revenue_generated
                existing.cost_generated = item.cost_generated
                existing.margin_generated = item.margin_generated
            else:
                db.add(
                    AnalyticsProductDaily(
                        date=item.date,
                        product_id=item.product_id,
                        quantity_sold=item.quantity_sold,
                        total_orders=item.total_orders,
                        unique_clients=item.unique_clients,
                        revenue_generated=item.revenue_generated,
                        cost_generated=item.cost_generated,
                        margin_generated=item.margin_generated,
                    )
                )

        db.flush()

    def list_by_product(
        self,
        db: Session,
        *,
        product_id: int,
        start_date: date,
        end_date: date,
        limit: int = 20,
    ) -> list[AnalyticsProductDaily]:

        stmt = (
            select(AnalyticsProductDaily)
            .where(AnalyticsProductDaily.product_id == product_id)
            .where(AnalyticsProductDaily.date >= start_date)
            .where(AnalyticsProductDaily.date <= end_date)
            .order_by(AnalyticsProductDaily.date.asc())
            .limit(limit)
        )

        return list(db.execute(stmt).scalars().all())

    def delete(
        self,
        db: Session,
        target_date: date,
        product_id: int,
    ) -> None:

        obj = self.get_by_date_and_product(db, target_date, product_id)

        if obj:
            db.delete(obj)
            db.flush()
            
    def list_by_date(
        self,
        db: Session,
        target_date: date,
    ) -> list[AnalyticsProductDaily]:
        stmt = (
            select(AnalyticsProductDaily)
            .where(AnalyticsProductDaily.date == target_date)
            .order_by(AnalyticsProductDaily.product_id.asc())
        )
        return list(db.execute(stmt).scalars().all())