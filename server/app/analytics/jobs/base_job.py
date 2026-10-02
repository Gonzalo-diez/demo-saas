from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.db.tenant_context import set_tenant, unscoped
from app.models.tenant_model import Tenant

# Importar todos los modelos aquí para que SQLAlchemy pueda resolver
# las relaciones entre modelos cuando el job corre con su propia sesión,
# sin pasar por main.py que normalmente registra todo.
import app.models  # noqa: F401
import app.analytics.models.analytics_product_daily_model  # noqa: F401
import app.analytics.models.analytics_daily_model  # noqa: F401
import app.analytics.models.analytics_sales_rep_daily_model  # noqa: F401
import app.analytics.models.analytics_client_daily_model  # noqa: F401
import app.analytics.models.analytics_zone_product_daily_model  # noqa: F401
import app.analytics.models.analytics_catalog_event_model  # noqa: F401


class BaseAnalyticsJob(ABC):
    """
    Base class for all analytics jobs.

    Enforces:
    - Consistent DB session lifecycle
    - Transaction handling
    - Standard execution entrypoint
    - Optional logging hooks
    """

    job_name: str = "base_analytics_job"

    def __init__(self) -> None:
        self.started_at: Optional[datetime] = None
        self.finished_at: Optional[datetime] = None

    def run(
        self,
        target_date: Optional[date] = None,
        tenant_id: Optional[int] = None,
    ) -> None:
        """
        Ejecuta el job para una fecha (por defecto hoy).

        - Con tenant_id: solo para esa distribuidora.
        - Sin tenant_id: para CADA tenant activo, cada uno en su propia
          sesión/transacción (un tenant que falla no frena a los demás).
        """
        target_date = target_date or date.today()

        tenant_ids = [tenant_id] if tenant_id is not None else self._active_tenant_ids()

        failures: list[tuple[int, Exception]] = []
        for tid in tenant_ids:
            try:
                self._run_for_tenant(tid, target_date)
            except Exception as e:  # ya logueado en _run_for_tenant
                failures.append((tid, e))

        if failures:
            tid, error = failures[0]
            raise RuntimeError(
                f"[{self.job_name}] falló para {len(failures)} tenant(s) "
                f"(primero: tenant {tid}): {error}"
            ) from error

    @staticmethod
    def _active_tenant_ids() -> list[int]:
        db: Session = SessionLocal()
        try:
            with unscoped(db):
                return list(
                    db.scalars(
                        select(Tenant.id).where(Tenant.is_active.is_(True)).order_by(Tenant.id)
                    ).all()
                )
        finally:
            db.close()

    def _run_for_tenant(self, tenant_id: int, target_date: date) -> None:
        self.started_at = datetime.utcnow()

        db: Session = SessionLocal()
        set_tenant(db, tenant_id)

        try:
            self._log_start(target_date, tenant_id)

            # Core execution
            self._run(db=db, target_date=target_date)

            db.commit()

            self.finished_at = datetime.utcnow()
            self._log_success(target_date, tenant_id)

        except Exception as e:
            db.rollback()
            self._log_error(target_date, e, tenant_id)
            raise

        finally:
            db.close()
            self.finished_at = datetime.utcnow()

    @abstractmethod
    def _run(self, db: Session, target_date: date) -> None:
        """
        Job-specific logic.

        Each job implements:
        - aggregations
        - repository calls
        - service orchestration
        """
        raise NotImplementedError

    def _log_start(self, target_date: date, tenant_id: int | None = None) -> None:
        print(f"[{self.job_name}] START tenant={tenant_id} date={target_date}")

    def _log_success(self, target_date: date, tenant_id: int | None = None) -> None:
        duration = self._duration_seconds()
        print(f"[{self.job_name}] SUCCESS tenant={tenant_id} date={target_date} duration={duration:.2f}s")

    def _log_error(self, target_date: date, error: Exception, tenant_id: int | None = None) -> None:
        print(f"[{self.job_name}] ERROR tenant={tenant_id} date={target_date} error={str(error)}")

    def _duration_seconds(self) -> float:
        if not self.started_at or not self.finished_at:
            return 0.0
        return (self.finished_at - self.started_at).total_seconds()