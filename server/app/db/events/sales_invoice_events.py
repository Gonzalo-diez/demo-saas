from __future__ import annotations
from datetime import date
from sqlalchemy import event
from sqlalchemy.orm import Session, attributes
from app.models.sales_invoice_model import SalesInvoice

def _schedule_reaggregation(session: Session, target_date: date) -> None:
    """
    Registra una fecha para re-agregar analytics después del commit.

    Usa el set 'pending_analytics_dates' en la sesión para acumular
    todas las fechas afectadas dentro de la misma transacción (ej: si
    se cancelan varios remitos a la vez, se agrega cada fecha una sola vez).
    """
    if not hasattr(session, "pending_analytics_dates"):
        session.pending_analytics_dates = set()

    session.pending_analytics_dates.add(target_date)


def _flush_pending_aggregations(session: Session) -> None:
    """
    Se ejecuta after_commit. Dispara el job para cada fecha pendiente.
    """
    pending: set[date] = getattr(session, "pending_analytics_dates", set())

    if not pending:
        return

    session.pending_analytics_dates = set()

    from app.analytics.jobs.run_daily_aggregations import RunDailyAggregationsJob

    job = RunDailyAggregationsJob()

    # El tenant de la sesión que hizo el cambio: solo se re-agrega ESE tenant
    # (sin esto el job recorrería todas las distribuidoras en cada remito).
    tenant_id = session.info.get("tenant_id")
    if tenant_id is None:
        return

    for target_date in pending:
        try:
            job.run(target_date=target_date, tenant_id=tenant_id)
        except Exception as e:
            # No levantamos la excepción — el commit principal ya ocurrió,
            # el job fallido se va a corregir en la próxima agregación nocturna.
            print(
                f"[sales_invoice_events] ERROR re-agregando analytics "
                f"para {target_date}: {e}"
            )

@event.listens_for(SalesInvoice, "after_insert")
def on_sales_invoice_insert(mapper, connection, target: SalesInvoice) -> None:
    """
    Nuevo remito creado → agregar su fecha después del commit.
    Solo remitos no cancelados (un remito se crea en draft o issued,
    nunca directamente en cancelled, pero lo chequeamos por seguridad).
    """
    if target.status == "cancelled":
        return

    session: Session = Session.object_session(target)
    if session is None:
        return

    _schedule_reaggregation(session, target.invoice_date)
    _register_after_commit_hook(session)


@event.listens_for(SalesInvoice, "after_update")
def on_sales_invoice_update(mapper, connection, target: SalesInvoice) -> None:
    """
    Remito actualizado → solo re-agregar si el status cambió.

    El único cambio que altera los analytics es la cancelación
    (issued → cancelled), que saca el remito del cómputo.
    Cambios en notas, PDF, email_sent_at, etc. no afectan analytics.
    """
    history = attributes.get_history(target, "status")

    if not history.deleted:
        return

    previous_status = history.deleted[0]
    current_status = target.status

    status_changed = previous_status != current_status
    involves_cancelled = "cancelled" in (previous_status, current_status)

    if not (status_changed and involves_cancelled):
        return

    session: Session = Session.object_session(target)
    if session is None:
        return

    _schedule_reaggregation(session, target.invoice_date)
    _register_after_commit_hook(session)

def _register_after_commit_hook(session: Session) -> None:
    """
    Registra el hook after_commit en la sesión, una sola vez.
    Evita registrarlo múltiples veces si varios remitos cambian
    en la misma transacción.
    """
    if getattr(session, "_analytics_hook_registered", False):
        return

    session._analytics_hook_registered = True

    @event.listens_for(session, "after_commit", once=True)
    def after_commit(sess: Session) -> None:
        sess._analytics_hook_registered = False
        _flush_pending_aggregations(sess)