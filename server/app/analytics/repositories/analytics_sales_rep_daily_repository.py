from __future__ import annotations
from datetime import date
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.analytics.models.analytics_sales_rep_daily_model import AnalyticsSalesRepDaily
from app.analytics.schemas.analytics_sales_rep_daily_schema import (
    AnalyticsSalesRepDailyCreate,
)

class AnalyticsSalesRepDailyRepository:
    def get_by_date_and_rep(
        self,
        db: Session,
        target_date: date,
        sales_rep_id: int,
    ) -> Optional[AnalyticsSalesRepDaily]:

        stmt = select(AnalyticsSalesRepDaily).where(
            AnalyticsSalesRepDaily.date == target_date,
            AnalyticsSalesRepDaily.sales_rep_id == sales_rep_id,
        )

        return db.execute(stmt).scalar_one_or_none()

    def upsert(
        self,
        db: Session,
        obj_in: AnalyticsSalesRepDailyCreate,
    ) -> AnalyticsSalesRepDaily:

        existing = self.get_by_date_and_rep(
            db,
            obj_in.date,
            obj_in.sales_rep_id,
        )

        if existing:
            existing.total_orders = obj_in.total_orders
            existing.total_clients = obj_in.total_clients
            existing.total_products_sold = obj_in.total_products_sold

            existing.revenue_generated = obj_in.revenue_generated
            existing.cost_generated = obj_in.cost_generated
            existing.margin_generated = obj_in.margin_generated

            db.flush()
            return existing

        db_obj = AnalyticsSalesRepDaily(
            date=obj_in.date,
            sales_rep_id=obj_in.sales_rep_id,
            total_orders=obj_in.total_orders,
            total_clients=obj_in.total_clients,
            total_products_sold=obj_in.total_products_sold,
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
        items: list[AnalyticsSalesRepDailyCreate],
    ) -> None:

        for item in items:
            existing = self.get_by_date_and_rep(
                db,
                item.date,
                item.sales_rep_id,
            )

            if existing:
                existing.total_orders = item.total_orders
                existing.total_clients = item.total_clients
                existing.total_products_sold = item.total_products_sold
                existing.revenue_generated = item.revenue_generated
                existing.cost_generated = item.cost_generated
                existing.margin_generated = item.margin_generated

            else:
                db.add(
                    AnalyticsSalesRepDaily(
                        date=item.date,
                        sales_rep_id=item.sales_rep_id,
                        total_orders=item.total_orders,
                        total_clients=item.total_clients,
                        total_products_sold=item.total_products_sold,
                        revenue_generated=item.revenue_generated,
                        cost_generated=item.cost_generated,
                        margin_generated=item.margin_generated,
                    )
                )

        db.flush()

    def list_by_rep(
        self,
        db: Session,
        *,
        sales_rep_id: int,
        start_date: date,
        end_date: date,
        limit: int = 31,
    ) -> list[AnalyticsSalesRepDaily]:

        stmt = (
            select(AnalyticsSalesRepDaily)
            .where(AnalyticsSalesRepDaily.sales_rep_id == sales_rep_id)
            .where(AnalyticsSalesRepDaily.date >= start_date)
            .where(AnalyticsSalesRepDaily.date <= end_date)
            .order_by(AnalyticsSalesRepDaily.date.asc())
            .limit(limit)
        )

        return list(db.execute(stmt).scalars().all())

    def delete(
        self,
        db: Session,
        target_date: date,
        sales_rep_id: int,
    ) -> None:

        obj = self.get_by_date_and_rep(db, target_date, sales_rep_id)

        if obj:
            db.delete(obj)
            db.flush()
            
    def list_by_date(
        self,
        db: Session,
        target_date: date,
    ) -> list[AnalyticsSalesRepDaily]:
        stmt = (
            select(AnalyticsSalesRepDaily)
            .where(AnalyticsSalesRepDaily.date == target_date)
            .order_by(AnalyticsSalesRepDaily.sales_rep_id.asc())
        )
        return list(db.execute(stmt).scalars().all())