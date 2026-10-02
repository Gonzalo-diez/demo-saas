from __future__ import annotations
from typing import List
from sqlalchemy.orm import Session
from app.analytics.repositories.analytics_catalog_event_repository import (
    AnalyticsCatalogEventRepository,
)
from app.analytics.schemas.analytics_catalog_event_schema import (
    AnalyticsCatalogEventCreate,
)
from app.analytics.constants.event_type_constant import AnalyticsEventType

class AnalyticsCatalogEventService:
    def __init__(self):
        self.repo = AnalyticsCatalogEventRepository()

    def create_event(
        self,
        db: Session,
        *,
        event_in: AnalyticsCatalogEventCreate,
    ):
        """
        Ingesta de un evento individual del catálogo.
        """
        self._normalize_event(event_in)
        
        event = self.repo.create(db, event_in)

        # (3) HOOK FUTURO: triggers de analytics
        # self._trigger_async_aggregation(event)

        return event

    def create_events_bulk(
        self,
        db: Session,
        *,
        events_in: List[AnalyticsCatalogEventCreate],
    ) -> None:
        """
        Ingesta masiva de eventos (tracking frontend, logs, etc).
        """

        for event in events_in:
            self._normalize_event(event)

        self.repo.bulk_create(db, events_in)

        # opcional: hook async
        # self._trigger_async_aggregation_bulk(events_in)

    def list_events(
        self,
        db: Session,
        **filters,
    ):
        return self.repo.list_events(db, **filters)

    def count_events(
        self,
        db: Session,
        **filters,
    ) -> int:
        return self.repo.count_events(db, **filters)

    def get_event(
        self,
        db: Session,
        event_id: int,
    ):
        return self.repo.get_by_id(db, event_id)

    def _normalize_event(
        self,
        event: AnalyticsCatalogEventCreate,
    ) -> None:
        """
        Limpieza y normalización de datos antes de persistir.
        """
        event.event_type = event.event_type.strip().lower()

        event.visitor_id = event.visitor_id.strip()
        event.session_id = event.session_id.strip()

        if event.source:
            event.source = event.source.strip().lower()

        if event.zone_h3_index:
            event.zone_h3_index = event.zone_h3_index.strip()

    def _trigger_async_aggregation(self, event):
        """
        Aquí luego conectas:
        - Celery task
        - Kafka event
        - Redis stream
        """
        pass

    def _trigger_async_aggregation_bulk(self, events):
        """
        Hook batch para procesamiento async.
        """
        pass