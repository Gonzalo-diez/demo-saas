from __future__ import annotations
from datetime import date
from decimal import Decimal
from typing import List
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.analytics.repositories.analytics_sales_rep_daily_repository import (
    AnalyticsSalesRepDailyRepository,
)
from app.analytics.schemas.analytics_sales_rep_daily_schema import (
    AnalyticsSalesRepDailyCreate,
    AnalyticsSalesRepDailyRead,
)
from app.analytics.services.sales_document_source import (
    sales_document_items_subquery,
    sales_documents_subquery,
)

class AnalyticsSalesRepDailyService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AnalyticsSalesRepDailyRepository()

    def get_daily_metrics(
        self,
        *,
        target_date: date,
    ) -> list[AnalyticsSalesRepDailyRead]:
        """
        Todos los vendedores con métricas para una fecha dada.
        Usado por GET /analytics/sales-reps/daily
        """
        items = self.repo.list_by_date(self.db, target_date)
        return [AnalyticsSalesRepDailyRead.model_validate(i) for i in items]

    def get_sales_rep_metrics(
        self,
        *,
        sales_rep_id: int,
        target_date: date,
    ) -> AnalyticsSalesRepDailyRead | None:
        """
        Métricas de un vendedor específico para una fecha.
        Usado por GET /analytics/sales-reps/daily/{sales_rep_id}
        """
        item = self.repo.get_by_date_and_rep(self.db, target_date, sales_rep_id)
        if not item:
            return None
        return AnalyticsSalesRepDailyRead.model_validate(item)

    def upsert_rep_daily(
        self,
        db: Session,
        *,
        data: AnalyticsSalesRepDailyCreate,
    ) -> AnalyticsSalesRepDailyRead:

        data = self._normalize(data)
        data = self._compute_metrics(data)

        obj = self.repo.upsert(db, data)

        return AnalyticsSalesRepDailyRead.model_validate(obj)

    def upsert_bulk(
        self,
        db: Session,
        *,
        items: List[AnalyticsSalesRepDailyCreate],
    ) -> List[AnalyticsSalesRepDailyRead]:

        results = []

        for item in items:
            item = self._normalize(item)
            item = self._compute_metrics(item)

            obj = self.repo.upsert(db, item)
            results.append(
                AnalyticsSalesRepDailyRead.model_validate(obj)
            )

        return results

    def get_rep_history(
        self,
        db: Session,
        *,
        sales_rep_id: int,
        start_date: date,
        end_date: date,
        limit: int = 20,
    ) -> List[AnalyticsSalesRepDailyRead]:

        data = self.repo.list_by_rep(
            db,
            sales_rep_id=sales_rep_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        return [
            AnalyticsSalesRepDailyRead.model_validate(d)
            for d in data
        ]

    def delete(
        self,
        db: Session,
        *,
        target_date: date,
        sales_rep_id: int,
    ) -> None:
        self.repo.delete(db, target_date, sales_rep_id)
        
    def compute_sales_rep_metrics(
        self,
        db: Session,
        *,
        target_date: date,
    ) -> list[AnalyticsSalesRepDailyCreate]:

        docs = sales_documents_subquery(confirmed_only=False)

        stmt = (
            select(
                docs.c.sales_rep_id,
                func.count(),
                func.count(
                    func.distinct(
                        docs.c.client_id
                    )
                ),
                func.coalesce(
                    func.sum(
                        docs.c.total_amount
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(
                        docs.c.total_cost
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(
                        docs.c.margin_amount
                    ),
                    0,
                ),
            )
            .where(
                docs.c.doc_date == target_date
            )
            .where(
                docs.c.sales_rep_id.is_not(None)
            )
            .group_by(
                docs.c.sales_rep_id
            )
        )

        rows = db.execute(stmt).all()

        items_src = sales_document_items_subquery(confirmed_only=False)

        results = []

        for (
            sales_rep_id,
            total_orders,
            total_clients,
            revenue,
            cost,
            margin,
        ) in rows:

            products_stmt = (
                select(
                    func.coalesce(
                        func.sum(
                            items_src.c.quantity
                        ),
                        0,
                    )
                )
                .where(
                    items_src.c.doc_date == target_date
                )
                .where(
                    items_src.c.sales_rep_id
                    == sales_rep_id
                )
            )

            total_products = (
                db.execute(products_stmt)
                .scalar_one()
            )

            results.append(
                AnalyticsSalesRepDailyCreate(
                    date=target_date,
                    sales_rep_id=sales_rep_id,
                    total_orders=total_orders or 0,
                    total_clients=total_clients or 0,
                    total_products_sold=total_products or 0,
                    revenue_generated=revenue or 0,
                    cost_generated=cost or 0,
                    margin_generated=margin or 0,
                )
            )

        return results
    
    def save_daily_snapshots(
        self,
        db: Session,
        *,
        metrics: list[AnalyticsSalesRepDailyCreate],
    ) -> list[AnalyticsSalesRepDailyRead]:

        return self.upsert_bulk(
            db,
            items=metrics,
        )

    def _normalize(
        self,
        data: AnalyticsSalesRepDailyCreate,
    ) -> AnalyticsSalesRepDailyCreate:
        data.total_orders = max(0, data.total_orders)
        data.total_clients = max(0, data.total_clients)
        data.total_products_sold = max(0, data.total_products_sold)

        return data

    def _compute_metrics(
        self,
        data: AnalyticsSalesRepDailyCreate,
    ) -> AnalyticsSalesRepDailyCreate:
        if data.margin_generated == 0:
            data.margin_generated = (
                data.revenue_generated - data.cost_generated
            )

        if data.revenue_generated < 0:
            data.revenue_generated = Decimal("0")

        if data.cost_generated < 0:
            data.cost_generated = Decimal("0")

        if data.total_orders > 0:
            pass

        return data