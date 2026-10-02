from __future__ import annotations
from datetime import date
from sqlalchemy.orm import Session
from app.analytics.jobs.base_job import BaseAnalyticsJob
from app.analytics.services.analytics_zone_product_daily_service import (
    AnalyticsZoneProductDailyService,
)

class ZoneProductDailyJob(BaseAnalyticsJob):
    """
    Aggregates daily product performance by geographic zone.

    Responsibility:
    - Compute product metrics grouped by zone (H3 / region / territory)
    - Persist results into analytics_zone_product_daily table
    """

    job_name = "zone_product_daily_job"
    
    def _run(self, db: Session, target_date: date) -> None:
        """
        Execute zone-product daily aggregation.
        """

        service = AnalyticsZoneProductDailyService(db)

        zone_product_metrics = service.compute_zone_product_metrics(db, target_date=target_date)

        service.save_daily_snapshots(
            db,
            metrics=zone_product_metrics,
        )