from __future__ import annotations
from datetime import date
from decimal import Decimal
from typing import List
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.analytics.repositories.analytics_zone_product_daily_repository import (
    AnalyticsZoneProductDailyRepository,
)
from app.analytics.schemas.analytics_zone_product_daily_schema import (
    AnalyticsZoneProductDailyCreate,
    AnalyticsZoneProductDailyRead,
)
from app.analytics.services.sales_document_source import (
    sales_document_items_subquery,
)
from app.models.client_branch_model import ClientBranch

class AnalyticsZoneProductDailyService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AnalyticsZoneProductDailyRepository()

    def get_daily_metrics(
        self,
        *,
        target_date: date,
    ) -> list[AnalyticsZoneProductDailyRead]:
        """
        Todas las zonas con métricas para una fecha dada.
        Usado por GET /analytics/zones/products/daily
        """
        items = self.repo.list_by_date(self.db, target_date)
        return [AnalyticsZoneProductDailyRead.model_validate(i) for i in items]

    def get_zone_metrics(
        self,
        *,
        h3_index: str,
        target_date: date,
    ) -> list[AnalyticsZoneProductDailyRead]:
        """
        Todos los productos de una zona específica para una fecha.
        Usado por GET /analytics/zones/products/daily/{h3_index}
        """
        items = self.repo.list_by_zone(
            self.db,
            h3_index=h3_index,
            start_date=target_date,
            end_date=target_date,
        )
        return [AnalyticsZoneProductDailyRead.model_validate(i) for i in items]

    def upsert_zone_product_daily(
        self,
        db: Session,
        *,
        data: AnalyticsZoneProductDailyCreate,
    ) -> AnalyticsZoneProductDailyRead:
        data = self._normalize(data)
        data = self._compute_metrics(data)

        obj = self.repo.upsert(db, data)

        return AnalyticsZoneProductDailyRead.model_validate(obj)

    def upsert_bulk(
        self,
        db: Session,
        *,
        items: List[AnalyticsZoneProductDailyCreate],
    ) -> List[AnalyticsZoneProductDailyRead]:
        results = []

        for item in items:
            item = self._normalize(item)
            item = self._compute_metrics(item)

            obj = self.repo.upsert(db, item)
            results.append(
                AnalyticsZoneProductDailyRead.model_validate(obj)
            )

        return results

    def get_zone_history(
        self,
        db: Session,
        *,
        h3_index: str,
        start_date: date,
        end_date: date,
        limit: int = 100,
    ) -> List[AnalyticsZoneProductDailyRead]:
        data = self.repo.list_by_zone(
            db,
            h3_index=h3_index,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        return [
            AnalyticsZoneProductDailyRead.model_validate(d)
            for d in data
        ]

    def get_product_geo_distribution(
        self,
        db: Session,
        *,
        product_id: int,
        start_date: date,
        end_date: date,
        limit: int = 200,
    ) -> List[AnalyticsZoneProductDailyRead]:
        data = self.repo.list_by_product(
            db,
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        return [
            AnalyticsZoneProductDailyRead.model_validate(d)
            for d in data
        ]

    def delete(
        self,
        db: Session,
        *,
        target_date: date,
        h3_index: str,
        product_id: int,
    ) -> None:
        self.repo.delete(db, target_date, h3_index, product_id)
        
    def compute_zone_product_metrics(
        self,
        db: Session,
        *,
        target_date: date,
    ) -> list[AnalyticsZoneProductDailyCreate]:

        items = sales_document_items_subquery(confirmed_only=False)

        stmt = (
            select(
                ClientBranch.h3_index,
                items.c.product_id,
                func.coalesce(
                    func.sum(
                        items.c.quantity
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(
                        items.c.subtotal
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(
                        items.c.subtotal_cost
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(
                        items.c.margin_amount
                    ),
                    0,
                ),
                func.count(
                    func.distinct(
                        items.c.client_id
                    )
                ),
            )
            .join(
                ClientBranch,
                ClientBranch.id
                == items.c.client_branch_id,
            )
            .where(
                items.c.doc_date == target_date
            )
            .where(
                ClientBranch.h3_index.is_not(None)
            )
            .where(
                items.c.product_id.is_not(None)
            )
            .group_by(
                ClientBranch.h3_index,
                items.c.product_id,
            )
        )

        rows = db.execute(stmt).all()

        return [
            AnalyticsZoneProductDailyCreate(
                date=target_date,
                h3_index=h3_index,
                product_id=product_id,
                quantity_sold=quantity_sold or 0,
                revenue_generated=revenue or 0,
                cost_generated=cost or 0,
                margin_generated=margin or 0,
                unique_clients=unique_clients or 0,
            )
            for (
                h3_index,
                product_id,
                quantity_sold,
                revenue,
                cost,
                margin,
                unique_clients,
            ) in rows
        ]
        
    def save_daily_snapshots(
        self,
        db: Session,
        *,
        metrics: list[AnalyticsZoneProductDailyCreate],
    ) -> list[AnalyticsZoneProductDailyRead]:

        return self.upsert_bulk(
            db,
            items=metrics,
        )

    def _normalize(
        self,
        data: AnalyticsZoneProductDailyCreate,
    ) -> AnalyticsZoneProductDailyCreate:

        # seguridad básica
        data.quantity_sold = max(0, data.quantity_sold)
        data.unique_clients = max(0, data.unique_clients)

        return data

    def _compute_metrics(
        self,
        data: AnalyticsZoneProductDailyCreate,
    ) -> AnalyticsZoneProductDailyCreate:
        if data.margin_generated == 0:
            data.margin_generated = (
                data.revenue_generated - data.cost_generated
            )

        if data.revenue_generated < 0:
            data.revenue_generated = Decimal("0")

        if data.cost_generated < 0:
            data.cost_generated = Decimal("0")

        return data