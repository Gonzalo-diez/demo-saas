from __future__ import annotations
from datetime import date
from sqlalchemy.orm import Session
from app.analytics.jobs.base_job import BaseAnalyticsJob
from app.analytics.services.analytics_sales_rep_daily_service import (
    AnalyticsSalesRepDailyService,
)

class SalesRepDailyJob(BaseAnalyticsJob):
    """
    Aggregates daily analytics per sales representative.

    Responsibility:
    - Compute sales metrics grouped by sales rep
    - Persist daily snapshots into analytics_sales_rep_daily table
    """

    job_name = "sales_rep_daily_job"

    def _run(self, db: Session, target_date: date) -> None:
        """
        Execute sales rep daily aggregation.
        """

        service = AnalyticsSalesRepDailyService(db)

        sales_rep_metrics = service.compute_sales_rep_metrics(db, target_date=target_date)

        service.save_daily_snapshots(
            db,
            metrics=sales_rep_metrics,
        )