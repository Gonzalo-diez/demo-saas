from __future__ import annotations
from datetime import date
from decimal import Decimal
from typing import List
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.analytics.repositories.analytics_product_daily_repository import (
    AnalyticsProductDailyRepository,
)
from app.analytics.schemas.analytics_product_daily_schema import (
    AnalyticsProductDailyCreate,
    AnalyticsProductDailyRead,
)
from app.analytics.services.sales_document_source import (
    sales_document_items_subquery,
)

class AnalyticsProductDailyService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AnalyticsProductDailyRepository()
        
    def get_daily_metrics(
        self,
        *,
        target_date: date,
    ) -> list[AnalyticsProductDailyRead]:
        """
        Todos los productos con métricas para una fecha dada.
        Usado por GET /analytics/products/daily
        """
        items = self.repo.list_by_date(self.db, target_date)
        return [AnalyticsProductDailyRead.model_validate(i) for i in items]

    def get_product_metrics(
        self,
        *,
        product_id: int,
        target_date: date,
    ) -> AnalyticsProductDailyRead | None:
        """
        Métricas de un producto específico para una fecha.
        Usado por GET /analytics/products/daily/{product_id}
        """
        item = self.repo.get_by_date_and_product(self.db, target_date, product_id)
        if not item:
            return None
        return AnalyticsProductDailyRead.model_validate(item)

    def upsert_product_daily(
        self,
        *,
        data: AnalyticsProductDailyCreate,
    ) -> AnalyticsProductDailyRead:

        data = self._normalize(data)
        data = self._compute_metrics(data)

        obj = self.repo.upsert(self.db, data)

        return AnalyticsProductDailyRead.model_validate(obj)

    def upsert_bulk(
        self,
        *,
        items: List[AnalyticsProductDailyCreate],
    ) -> List[AnalyticsProductDailyRead]:

        results = []

        for item in items:
            item = self._normalize(item)
            item = self._compute_metrics(item)

            obj = self.repo.upsert(self.db, item)
            results.append(AnalyticsProductDailyRead.model_validate(obj))

        return results

    def get_product_history(
        self,
        *,
        product_id: int,
        start_date: date,
        end_date: date,
        limit: int = 20,
    ) -> List[AnalyticsProductDailyRead]:

        data = self.repo.list_by_product(
            self.db,
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        return [
            AnalyticsProductDailyRead.model_validate(d)
            for d in data
        ]

    def delete(
        self,
        *,
        target_date: date,
        product_id: int,
    ) -> None:

        self.repo.delete(self.db, target_date, product_id)
        
    def compute_product_metrics(
        self,
        *,
        target_date: date,
    ) -> list[AnalyticsProductDailyCreate]:

        items = sales_document_items_subquery(confirmed_only=False)

        stmt = (
            select(
                items.c.product_id,
                func.coalesce(
                    func.sum(items.c.quantity),
                    0,
                ),
                func.coalesce(
                    func.sum(items.c.subtotal),
                    0,
                ),
                func.coalesce(
                    func.sum(items.c.subtotal_cost),
                    0,
                ),
                func.coalesce(
                    func.sum(items.c.margin_amount),
                    0,
                ),
            )
            .where(
                items.c.doc_date == target_date
            )
            .where(
                items.c.product_id.is_not(None)
            )
            .group_by(
                items.c.product_id
            )
        )

        rows = self.db.execute(stmt).all()

        return [
            AnalyticsProductDailyCreate(
                date=target_date,
                product_id=product_id,
                quantity_sold=quantity_sold or 0,
                revenue_generated=revenue or 0,
                cost_generated=cost or 0,
                margin_generated=margin or 0,
            )
            for (
                product_id,
                quantity_sold,
                revenue,
                cost,
                margin,
            ) in rows
        ]
        
    def save_daily_snapshots(
        self,
        *,
        metrics: list[AnalyticsProductDailyCreate],
    ) -> list[AnalyticsProductDailyRead]:

        return self.upsert_bulk(
            items=metrics,
        )

    def _normalize(
        self,
        data: AnalyticsProductDailyCreate,
    ) -> AnalyticsProductDailyCreate:

        # seguridad básica
        data.quantity_sold = max(0, data.quantity_sold)

        return data

    def _compute_metrics(
        self,
        data: AnalyticsProductDailyCreate,
    ) -> AnalyticsProductDailyCreate:

        # margin fallback si no viene bien calculado
        if data.margin_generated == 0:
            data.margin_generated = (
                data.revenue_generated - data.cost_generated
            )

        # sanity check
        if data.revenue_generated < 0:
            data.revenue_generated = Decimal("0")

        if data.cost_generated < 0:
            data.cost_generated = Decimal("0")

        return data