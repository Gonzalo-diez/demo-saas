from __future__ import annotations
from datetime import date
from sqlalchemy.orm import Session
from app.analytics.jobs.base_job import BaseAnalyticsJob
from app.analytics.services.analytics_daily_service import AnalyticsDailyService

class DailyJob(BaseAnalyticsJob):
    """
    Agrega métricas globales diarias desde SalesInvoice.

    Responsibilities:
    - Total de órdenes, clientes, productos vendidos
    - Revenue, costo, margen y ticket promedio del día
    """

    job_name = "daily_analytics"

    def _run(self, db: Session, target_date: date) -> None:
        service = AnalyticsDailyService()

        service.aggregate_date(
            db,
            target_date=target_date,
        )