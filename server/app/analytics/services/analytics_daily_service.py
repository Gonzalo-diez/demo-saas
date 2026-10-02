from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.repositories.analytics_daily_repository import (
    AnalyticsDailyRepository,
)
from app.analytics.schemas.analytics_daily_schema import (
    AnalyticsDailyCreate,
    AnalyticsDailyRead,
)
from app.models.sales_invoice_model import SalesInvoice


class AnalyticsDailyService:
    def __init__(self):
        self.repo = AnalyticsDailyRepository()

    def aggregate_date(
        self,
        db: Session,
        *,
        target_date: date,
    ) -> AnalyticsDailyRead:
        """
        Recalcula completamente un día y hace upsert.
        """

        snapshot = self.compute_daily_metrics(
            db,
            target_date=target_date,
        )

        return self.upsert_daily_snapshot(
            db,
            data=snapshot,
        )

    def compute_daily_metrics(
        self,
        db: Session,
        *,
        target_date: date,
    ) -> AnalyticsDailyCreate:
        """
        Construye métricas diarias desde SalesInvoice.
        """

        stmt = (
            select(
                func.count(SalesInvoice.id),
                func.count(
                    func.distinct(
                        SalesInvoice.client_id
                    )
                ),
                func.coalesce(
                    func.sum(SalesInvoice.total_amount),
                    0,
                ),
                func.coalesce(
                    func.sum(SalesInvoice.total_cost),
                    0,
                ),
                func.coalesce(
                    func.sum(SalesInvoice.margin_amount),
                    0,
                ),
            )
            .where(
                SalesInvoice.invoice_date == target_date
            )
            .where(
                SalesInvoice.status != "cancelled"
            )
        )

        (
            total_orders,
            total_clients,
            revenue_generated,
            cost_generated,
            margin_generated,
        ) = db.execute(stmt).one()

        total_products_sold = self._compute_total_products_sold(
            db,
            target_date=target_date,
        )

        return AnalyticsDailyCreate(
            date=target_date,
            total_orders=total_orders or 0,
            total_clients=total_clients or 0,
            total_products_sold=total_products_sold,
            revenue_generated=Decimal(
                revenue_generated or 0
            ),
            cost_generated=Decimal(
                cost_generated or 0
            ),
            margin_generated=Decimal(
                margin_generated or 0
            ),
            average_ticket=Decimal("0"),
        )

    def upsert_daily_snapshot(
        self,
        db: Session,
        *,
        data: AnalyticsDailyCreate,
    ) -> AnalyticsDailyRead:

        data = self._normalize(data)

        data = self._compute_derived_metrics(data)

        obj = self.repo.upsert(
            db,
            data,
        )

        return AnalyticsDailyRead.model_validate(
            obj
        )

    def _compute_total_products_sold(
        self,
        db: Session,
        *,
        target_date: date,
    ) -> int:
        from app.models.sales_invoice_item_model import (
            SalesInvoiceItem,
        )

        stmt = (
            select(
                func.coalesce(
                    func.sum(
                        SalesInvoiceItem.quantity
                    ),
                    0,
                )
            )
            .join(
                SalesInvoice,
                SalesInvoice.id
                == SalesInvoiceItem.sales_invoice_id,
            )
            .where(
                SalesInvoice.invoice_date
                == target_date
            )
            .where(
                SalesInvoice.status != "cancelled"
            )
        )

        return int(
            db.execute(stmt).scalar_one() or 0
        )

    def _normalize(
        self,
        data: AnalyticsDailyCreate,
    ) -> AnalyticsDailyCreate:
        return data

    def _compute_derived_metrics(
        self,
        data: AnalyticsDailyCreate,
    ) -> AnalyticsDailyCreate:

        if data.margin_generated == 0:
            data.margin_generated = (
                data.revenue_generated
                - data.cost_generated
            )

        if data.total_orders > 0:
            data.average_ticket = (
                data.revenue_generated
                / data.total_orders
            ).quantize(
                Decimal("0.01")
            )
        else:
            data.average_ticket = Decimal("0")

        return data