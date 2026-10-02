from __future__ import annotations
from datetime import date
from sqlalchemy.orm import Session
from app.analytics.jobs.base_job import BaseAnalyticsJob
from app.analytics.services.analytics_product_daily_service import (
    AnalyticsProductDailyService,
)

class ProductDailyJob(BaseAnalyticsJob):
    """
    Aggregates daily product analytics.

    Responsibilities:
    - Build product-level daily snapshots
    - Persist aggregated metrics into analytics_product_daily table
    """

    job_name = "product_daily_job"

    def _run(self, db: Session, target_date: date) -> None:
        """
        Executes product daily aggregation for a specific date.
        """

        service = AnalyticsProductDailyService(db)

        # 1. Build base aggregation (sales, quantity, revenue, etc.)
        product_metrics = service.compute_product_metrics(
            target_date=target_date,
        )

        # 2. Persist daily snapshot
        service.save_daily_snapshots(
            metrics=product_metrics,
        )