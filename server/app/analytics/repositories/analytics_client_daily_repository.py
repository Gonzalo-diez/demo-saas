from __future__ import annotations
from datetime import date
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.analytics.models.analytics_client_daily_model import AnalyticsClientDaily
from app.analytics.schemas.analytics_client_daily_schema import (
    AnalyticsClientDailyCreate,
)

class AnalyticsClientDailyRepository:
    def get_by_date_and_client(
        self,
        db: Session,
        target_date: date,
        client_id: int,
    ) -> Optional[AnalyticsClientDaily]:
        stmt = select(AnalyticsClientDaily).where(
            AnalyticsClientDaily.date == target_date,
            AnalyticsClientDaily.client_id == client_id,
        )

        return db.execute(stmt).scalar_one_or_none()

    def upsert(
        self,
        db: Session,
        obj_in: AnalyticsClientDailyCreate,
    ) -> AnalyticsClientDaily:
        existing = self.get_by_date_and_client(
            db,
            obj_in.date,
            obj_in.client_id,
        )

        if existing:
            existing.total_orders = obj_in.total_orders
            existing.revenue_generated = obj_in.revenue_generated
            existing.cost_generated = obj_in.cost_generated
            existing.margin_generated = obj_in.margin_generated
            existing.products_bought = obj_in.products_bought
            existing.unique_products_count = obj_in.unique_products_count
            existing.categories_summary = obj_in.categories_summary

            db.flush()
            return existing

        db_obj = AnalyticsClientDaily(
            date=obj_in.date,
            client_id=obj_in.client_id,
            total_orders=obj_in.total_orders,
            revenue_generated=obj_in.revenue_generated,
            cost_generated=obj_in.cost_generated,
            margin_generated=obj_in.margin_generated,
            products_bought=obj_in.products_bought,
            unique_products_count=obj_in.unique_products_count,
            categories_summary=obj_in.categories_summary,
        )

        db.add(db_obj)
        db.flush()

        return db_obj

    def bulk_upsert(
        self,
        db: Session,
        items: list[AnalyticsClientDailyCreate],
    ) -> None:
        for item in items:
            existing = self.get_by_date_and_client(
                db,
                item.date,
                item.client_id,
            )

            if existing:
                existing.total_orders = item.total_orders
                existing.revenue_generated = item.revenue_generated
                existing.cost_generated = item.cost_generated
                existing.margin_generated = item.margin_generated
                existing.products_bought = item.products_bought
                existing.unique_products_count = item.unique_products_count
                existing.categories_summary = item.categories_summary
            else:
                db.add(
                    AnalyticsClientDaily(
                        date=item.date,
                        client_id=item.client_id,
                        total_orders=item.total_orders,
                        revenue_generated=item.revenue_generated,
                        cost_generated=item.cost_generated,
                        margin_generated=item.margin_generated,
                        products_bought=item.products_bought,
                        unique_products_count=item.unique_products_count,
                        categories_summary=item.categories_summary,
                    )
                )

        db.flush()

    def list_by_client(
        self,
        db: Session,
        *,
        client_id: int,
        start_date: date,
        end_date: date,
        limit: int = 90,
    ) -> list[AnalyticsClientDaily]:
        stmt = (
            select(AnalyticsClientDaily)
            .where(AnalyticsClientDaily.client_id == client_id)
            .where(AnalyticsClientDaily.date >= start_date)
            .where(AnalyticsClientDaily.date <= end_date)
            .order_by(AnalyticsClientDaily.date.asc())
            .limit(limit)
        )

        return list(db.execute(stmt).scalars().all())

    def list_by_date(
        self,
        db: Session,
        target_date: date,
    ) -> list[AnalyticsClientDaily]:
        stmt = (
            select(AnalyticsClientDaily)
            .where(AnalyticsClientDaily.date == target_date)
            .order_by(AnalyticsClientDaily.client_id.asc())
        )

        return list(db.execute(stmt).scalars().all())

    def delete(
        self,
        db: Session,
        target_date: date,
        client_id: int,
    ) -> None:
        obj = self.get_by_date_and_client(db, target_date, client_id)

        if obj:
            db.delete(obj)
            db.flush()