from __future__ import annotations
from datetime import date
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.analytics.models.analytics_zone_product_daily_model import AnalyticsZoneProductDaily
from app.analytics.schemas.analytics_zone_product_daily_schema import (
    AnalyticsZoneProductDailyCreate,
)

class AnalyticsZoneProductDailyRepository:
    def get_by_key(
        self,
        db: Session,
        target_date: date,
        h3_index: str,
        product_id: int,
    ) -> Optional[AnalyticsZoneProductDaily]:

        stmt = select(AnalyticsZoneProductDaily).where(
            AnalyticsZoneProductDaily.date == target_date,
            AnalyticsZoneProductDaily.h3_index == h3_index,
            AnalyticsZoneProductDaily.product_id == product_id,
        )

        return db.execute(stmt).scalar_one_or_none()

    def upsert(
        self,
        db: Session,
        obj_in: AnalyticsZoneProductDailyCreate,
    ) -> AnalyticsZoneProductDaily:

        existing = self.get_by_key(
            db,
            obj_in.date,
            obj_in.h3_index,
            obj_in.product_id,
        )

        if existing:
            existing.quantity_sold = obj_in.quantity_sold
            existing.total_orders = obj_in.total_orders
            existing.revenue_generated = obj_in.revenue_generated
            existing.cost_generated = obj_in.cost_generated
            existing.margin_generated = obj_in.margin_generated
            existing.unique_clients = obj_in.unique_clients

            db.flush()
            return existing

        db_obj = AnalyticsZoneProductDaily(
            date=obj_in.date,
            h3_index=obj_in.h3_index,
            product_id=obj_in.product_id,
            quantity_sold=obj_in.quantity_sold,
            total_orders=obj_in.total_orders,
            revenue_generated=obj_in.revenue_generated,
            cost_generated=obj_in.cost_generated,
            margin_generated=obj_in.margin_generated,
            unique_clients=obj_in.unique_clients,
        )

        db.add(db_obj)
        db.flush()

        return db_obj

    def bulk_upsert(
        self,
        db: Session,
        items: list[AnalyticsZoneProductDailyCreate],
    ) -> None:

        for item in items:
            existing = self.get_by_key(
                db,
                item.date,
                item.h3_index,
                item.product_id,
            )

            if existing:
                existing.quantity_sold = item.quantity_sold
                existing.total_orders = item.total_orders
                existing.revenue_generated = item.revenue_generated
                existing.cost_generated = item.cost_generated
                existing.margin_generated = item.margin_generated
                existing.unique_clients = item.unique_clients

            else:
                db.add(
                    AnalyticsZoneProductDaily(
                        date=item.date,
                        h3_index=item.h3_index,
                        product_id=item.product_id,
                        quantity_sold=item.quantity_sold,
                        total_orders=item.total_orders,
                        revenue_generated=item.revenue_generated,
                        cost_generated=item.cost_generated,
                        margin_generated=item.margin_generated,
                        unique_clients=item.unique_clients,
                    )
                )

        db.flush()

    def list_by_zone(
        self,
        db: Session,
        *,
        h3_index: str,
        start_date: date,
        end_date: date,
        limit: int = 100,
    ) -> list[AnalyticsZoneProductDaily]:

        stmt = (
            select(AnalyticsZoneProductDaily)
            .where(AnalyticsZoneProductDaily.h3_index == h3_index)
            .where(AnalyticsZoneProductDaily.date >= start_date)
            .where(AnalyticsZoneProductDaily.date <= end_date)
            .order_by(AnalyticsZoneProductDaily.date.asc())
            .limit(limit)
        )

        return list(db.execute(stmt).scalars().all())

    def list_by_product(
        self,
        db: Session,
        *,
        product_id: int,
        start_date: date,
        end_date: date,
        limit: int = 200,
    ) -> list[AnalyticsZoneProductDaily]:

        stmt = (
            select(AnalyticsZoneProductDaily)
            .where(AnalyticsZoneProductDaily.product_id == product_id)
            .where(AnalyticsZoneProductDaily.date >= start_date)
            .where(AnalyticsZoneProductDaily.date <= end_date)
            .order_by(AnalyticsZoneProductDaily.date.asc())
            .limit(limit)
        )

        return list(db.execute(stmt).scalars().all())

    def delete(
        self,
        db: Session,
        target_date: date,
        h3_index: str,
        product_id: int,
    ) -> None:

        obj = self.get_by_key(db, target_date, h3_index, product_id)

        if obj:
            db.delete(obj)
            db.flush()
            
    def list_by_date(
        self,
        db: Session,
        target_date: date,
    ) -> list[AnalyticsZoneProductDaily]:
        stmt = (
            select(AnalyticsZoneProductDaily)
            .where(AnalyticsZoneProductDaily.date == target_date)
            .order_by(
                AnalyticsZoneProductDaily.h3_index.asc(),
                AnalyticsZoneProductDaily.product_id.asc(),
            )
        )
        return list(db.execute(stmt).scalars().all())