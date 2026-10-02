from __future__ import annotations
from datetime import date
from sqlalchemy.orm import Session
from app.analytics.jobs.base_job import BaseAnalyticsJob
from app.analytics.services.analytics_client_daily_service import AnalyticsClientDailyService

class ClientDailyJob(BaseAnalyticsJob):
    """
    Agrega métricas globales diarias desde Client.

    Responsibilities:
    - Mejores clientes, clientes perdidos, clientes nuevos
    - Frecuencia de compra, productos comprados y ticket promedio por cliente
    """

    job_name = "client_daily_analytics"

    def _run(self, db: Session, target_date: date) -> None:
        service = AnalyticsClientDailyService(db)

        service.aggregate_date(
            db,
            target_date=target_date,
        )