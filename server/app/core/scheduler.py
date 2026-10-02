from __future__ import annotations
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
scheduler = AsyncIOScheduler()
logger = logging.getLogger(__name__)
BUSINESS_TZ = "America/Argentina/Buenos_Aires"

def setup_scheduler() -> None:
    from app.analytics.jobs.run_daily_aggregations import RunDailyAggregationsJob

    scheduler.add_job(
        _run_daily_aggregations,
        trigger=CronTrigger(
            hour=2,
            minute=0,
            timezone="America/Argentina/Buenos_Aires",
        ),
        id="run_daily_aggregations",
        name="Agregaciones diarias de analytics",
        replace_existing=True,
        misfire_grace_time=3600,  # si el server estaba caído, lo ejecuta hasta 1h después
    )

    # Barrido diario de notificaciones (stock y cheques): cubre lo que depende
    # de la fecha (cheques que entran en su ventana de vencimiento) y lo que
    # no pasó por los avisos en tiempo real (imports, ediciones directas).
    scheduler.add_job(
        _run_notifications_sync,
        trigger=CronTrigger(
            hour=8,
            minute=0,
            timezone=BUSINESS_TZ,
        ),
        id="run_notifications_sync",
        name="Barrido diario de notificaciones (stock y cheques)",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # Una pasada al arrancar, para que tras un deploy los avisos ya estén al día.
    from datetime import datetime, timedelta
    from apscheduler.triggers.date import DateTrigger

    scheduler.add_job(
        _run_notifications_sync,
        trigger=DateTrigger(run_date=datetime.now().astimezone() + timedelta(seconds=20)),
        id="run_notifications_sync_startup",
        name="Sincronización inicial de notificaciones",
        replace_existing=True,
    )

def _run_notifications_sync() -> None:
    from sqlalchemy import select
    from app.db.base import SessionLocal
    from app.db.tenant_context import set_tenant, unscoped
    from app.models.tenant_model import Tenant
    from app.services.notification_alert_service import NotificationAlertService

    # 1) tenants activos
    db = SessionLocal()
    try:
        with unscoped(db):
            tenant_ids = list(
                db.scalars(select(Tenant.id).where(Tenant.is_active.is_(True))).all()
            )
    finally:
        db.close()

    # 2) una sesión (y transacción) por tenant: si uno falla, siguen los demás
    for tenant_id in tenant_ids:
        db = SessionLocal()
        set_tenant(db, tenant_id)
        try:
            result = NotificationAlertService(db).run_full_sync()
            db.commit()
            logger.info("Sincronización de notificaciones OK (tenant %s): %s", tenant_id, result)
        except Exception:
            db.rollback()
            logger.exception("Falló la sincronización de notificaciones (tenant %s)", tenant_id)
        finally:
            db.close()

def _run_daily_aggregations() -> None:
    from datetime import date, timedelta
    from app.analytics.jobs.run_daily_aggregations import RunDailyAggregationsJob

    yesterday = date.today() - timedelta(days=1)
    RunDailyAggregationsJob().run(target_date=yesterday)