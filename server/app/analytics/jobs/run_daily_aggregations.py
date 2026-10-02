from __future__ import annotations
from datetime import date
from sqlalchemy.orm import Session
from app.analytics.jobs.base_job import BaseAnalyticsJob
from app.db.tenant_context import require_tenant_id
from app.analytics.jobs.daily_job import DailyJob
from app.analytics.jobs.product_daily_job import ProductDailyJob
from app.analytics.jobs.sales_rep_daily_job import SalesRepDailyJob
from app.analytics.jobs.zone_product_daily_job import ZoneProductDailyJob
from app.analytics.jobs.client_daily_job import ClientDailyJob

class RunDailyAggregationsJob(BaseAnalyticsJob):
    """
    Maestra que ejecuta todos los jobs de agregación diaria en orden.

    Responsabilidades:
    - Ejecutar todos los jobs de agregación diaria en orden
    - Aislar fallos de cada job para que no afecten a los demás
    - Un único punto de entrada para ejecutar todas las agregaciones diarias
    """

    job_name = "run_daily_aggregations"

    def _run(self, db: Session, target_date: date) -> None:
        # Cada sub-job abre su propia sesión: se le pasa el tenant explícitamente.
        tenant_id = require_tenant_id(db)
        jobs: list[tuple[str, BaseAnalyticsJob]] = [
            ("daily_analytics",    DailyJob()),
            ("product_daily_job",  ProductDailyJob()),
            ("sales_rep_daily_job", SalesRepDailyJob()),
            ("zone_product_daily_job", ZoneProductDailyJob()),
            ("client_daily_job", ClientDailyJob()),
        ]

        for job_name, job in jobs:
            try:
                print(f"\n[RUNNER] Starting {job_name} for {target_date}")

                job.run(target_date=target_date, tenant_id=tenant_id)

                print(f"[RUNNER] Completed {job_name} successfully")

            except Exception as e:
                print(f"[RUNNER] ERROR in {job_name}: {str(e)}")
                print(f"[RUNNER] Continuing with next job...\n")