"""
Motor de avisos: decide CUÁNDO corresponde una notificación (stock bajo,
cheque por vencer, etc.) y mantiene la tabla `notifications` al día.

Se dispara de dos formas, que se complementan:
  1) En tiempo real, enganchado donde cambia el dato (movimientos de stock,
     alta/depósito/acreditación/rechazo de cheques) -> métodos `safe_*`.
  2) Un barrido diario (scheduler) que reconcilia todo -> `run_full_sync`.
     Es el que cubre lo que depende de la fecha (un cheque que entra en su
     ventana de vencimiento sin que nadie lo toque) y cualquier camino que
     no pase por el hook en tiempo real (imports, ediciones directas).

Todo es idempotente: correrlo dos veces seguidas no duplica avisos.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.constants.notifications_constant import (
    ENTITY_TYPE_CHECK,
    ENTITY_TYPE_PRODUCT,
    EVENT_NOTIFICATION_TYPES,
    NOTIFICATION_TYPE_META,
)
from app.core.config import get_settings
from app.models.check_model import Check
from app.models.notification_model import Notification
from app.models.product_model import Product
from app.repositories.notification_repository import NotificationRepository

logger = logging.getLogger(__name__)

EVENT_ARCHIVE_DAYS = 30


# ----------------------------------------------------------------------
# Helpers de fecha y formato
# ----------------------------------------------------------------------

def today_local() -> date:
    """'Hoy' en la zona horaria del negocio (no la del servidor)."""
    settings = get_settings()
    try:
        tz = ZoneInfo(settings.NOTIFICATIONS_TIMEZONE)
    except ZoneInfoNotFoundError:
        # Argentina no tiene horario de verano: UTC-3 fijo como respaldo
        # si la imagen no trae la base de zonas horarias.
        tz = timezone(timedelta(hours=-3))
    return datetime.now(tz).date()


def format_ars(amount) -> str:
    value = Decimal(str(amount)).quantize(Decimal("0.01"))
    text = f"{value:,.2f}"  # 1,234.56
    text = text.replace(",", "_").replace(".", ",").replace("_", ".")  # 1.234,56
    return f"$ {text}"


def format_date(value: date) -> str:
    return value.strftime("%d/%m/%Y")


def _units(n) -> str:
    n = int(n)
    return f"{n} unidad" if n == 1 else f"{n} unidades"


# ----------------------------------------------------------------------
# Reglas (funciones puras, fáciles de testear)
# ----------------------------------------------------------------------

def get_stock_alert_type(
    stock_current,
    stock_min,
    *,
    margin_percent: int,
    is_active: bool = True,
) -> str | None:
    """
    - stock_out:      no hay stock (== 0)
    - stock_low:      stock <= mínimo
    - stock_near_min: stock hasta `margin_percent`% por encima del mínimo
    Sin mínimo cargado (0) solo se avisa cuando se queda sin stock.
    Productos inactivos (borradores, dados de baja) no avisan.
    """
    if not is_active:
        return None

    stock = stock_current or 0
    minimum = stock_min or 0

    if stock <= 0:
        return "stock_out"
    if minimum <= 0:
        return None
    if stock <= minimum:
        return "stock_low"
    if stock * 100 <= minimum * (100 + margin_percent):
        return "stock_near_min"
    return None


def get_check_alert_type(
    *,
    status: str,
    payment_date: date,
    due_date: date,
    today: date,
    days_before: int,
) -> str | None:
    """
    Solo cheques 'pendiente' (los depositados/acreditados/rechazados ya no
    requieren una acción). De más a menos urgente:
    - check_overdue:  ya pasó el vencimiento y sigue pendiente
    - check_due_soon: el vencimiento cae dentro de los próximos `days_before` días
    - check_payable:  ya es cobrable (llegó la fecha de pago)
    - check_upcoming: será cobrable dentro de los próximos `days_before` días
    """
    if status != "pendiente":
        return None

    window_end = today + timedelta(days=days_before)

    if due_date < today:
        return "check_overdue"
    if due_date <= window_end:
        return "check_due_soon"
    if payment_date <= today:
        return "check_payable"
    if payment_date <= window_end:
        return "check_upcoming"
    return None


# ----------------------------------------------------------------------
# Textos
# ----------------------------------------------------------------------

def _stock_content(alert_type: str, product: Product) -> tuple[str, str, dict]:
    stock = int(product.stock_current or 0)
    minimum = int(product.stock_min or 0)
    sku = f" (SKU {product.sku})" if product.sku else ""

    if alert_type == "stock_out":
        title = f"Sin stock: {product.name}"
        message = f"El producto {product.name}{sku} se quedó sin stock."
    elif alert_type == "stock_low":
        title = f"Stock bajo: {product.name}"
        message = (
            f"Quedan {_units(stock)} de {product.name}{sku}, "
            f"en o por debajo del mínimo ({minimum})."
        )
    else:
        title = f"Cerca del stock mínimo: {product.name}"
        message = (
            f"Quedan {_units(stock)} de {product.name}{sku}; "
            f"el mínimo es {minimum}."
        )

    data = {
        "product_id": product.id,
        "product_name": product.name,
        "sku": product.sku,
        "stock_current": stock,
        "stock_min": minimum,
    }
    return title, message, data


def _check_counterparty(check: Check) -> str:
    if check.direction == "received":
        return check.client.name if check.client else f"cliente #{check.client_id}"
    return check.supplier.name if check.supplier else f"proveedor #{check.supplier_id}"


def _days_label(target: date, today: date) -> str:
    days = (target - today).days
    if days <= 0:
        return "hoy"
    if days == 1:
        return "mañana"
    return f"en {days} días"


def _check_content(alert_type: str, check: Check, today: date) -> tuple[str, str, dict]:
    who = _check_counterparty(check)
    amount = format_ars(check.amount)
    number = check.check_number
    received = check.direction == "received"
    origin = f"de {who}" if received else f"emitido a {who}"

    if alert_type == "check_overdue":
        title = "Cheque recibido vencido" if received else "Cheque emitido vencido"
        message = (
            f"El cheque #{number} {origin} por {amount} venció el "
            f"{format_date(check.due_date)} y sigue pendiente."
        )
    elif alert_type == "check_due_soon":
        title = "Cheque recibido por vencer" if received else "Cheque emitido por vencer"
        message = (
            f"El cheque #{number} {origin} por {amount} vence "
            f"{_days_label(check.due_date, today)} ({format_date(check.due_date)})."
        )
        if received:
            message += " Conviene depositarlo antes."
    elif alert_type == "check_payable":
        if received:
            title = "Cheque listo para depositar"
            message = (
                f"El cheque #{number} {origin} por {amount} ya se puede "
                f"depositar (desde el {format_date(check.payment_date)})."
            )
        else:
            title = "Cheque emitido ya cobrable"
            message = (
                f"El cheque #{number} {origin} por {amount} ya puede ser "
                f"presentado al cobro (desde el {format_date(check.payment_date)}). "
                f"Asegurá fondos en la cuenta."
            )
    else:  # check_upcoming
        if received:
            title = "Cheque próximo a ser cobrable"
            message = (
                f"El cheque #{number} {origin} por {amount} se podrá depositar "
                f"{_days_label(check.payment_date, today)} ({format_date(check.payment_date)})."
            )
        else:
            title = "Cheque emitido próximo a debitarse"
            message = (
                f"El cheque #{number} {origin} por {amount} se podrá cobrar "
                f"{_days_label(check.payment_date, today)} ({format_date(check.payment_date)}). "
                f"Asegurá fondos en la cuenta."
            )

    return title, message, _check_data(check, who)


def _check_data(check: Check, who: str) -> dict:
    return {
        "check_id": check.id,
        "direction": check.direction,
        "check_number": check.check_number,
        "amount": str(check.amount),
        "payment_date": check.payment_date.isoformat(),
        "due_date": check.due_date.isoformat(),
        "client_id": check.client_id,
        "supplier_id": check.supplier_id,
        "counterparty_name": who,
    }


# ----------------------------------------------------------------------
# Servicio
# ----------------------------------------------------------------------

class NotificationAlertService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificationRepository(db)
        self.settings = get_settings()

    # -- núcleo --------------------------------------------------------

    def _upsert(
        self,
        *,
        dedup_key: str,
        alert_type: str,
        title: str,
        message: str,
        entity_type: str,
        entity_id: int,
        data: dict,
    ) -> Notification:
        category, severity, level = NOTIFICATION_TYPE_META[alert_type]

        existing = self.repo.get_active_by_dedup_key(dedup_key)
        if existing is None:
            return self.repo.create(
                category=category,
                type_=alert_type,
                severity=severity,
                level=level,
                title=title,
                message=message,
                dedup_key=dedup_key,
                entity_type=entity_type,
                entity_id=entity_id,
                data=data,
            )

        escalated = level > existing.level
        unchanged = (
            existing.type == alert_type
            and existing.title == title
            and existing.message == message
        )
        if unchanged:
            return existing

        existing.type = alert_type
        existing.severity = severity
        existing.level = level
        existing.title = title
        existing.message = message
        existing.data = data

        if escalated:
            # Empeoró: vuelve a aparecer como no leída para todos.
            existing.notified_at = datetime.now(timezone.utc)
            self.repo.clear_reads(existing.id)

        self.db.flush()
        return existing

    def _resolve(self, dedup_key: str) -> None:
        self.repo.resolve_by_dedup_key(dedup_key, datetime.now(timezone.utc))

    # -- stock ---------------------------------------------------------

    def _stock_alert_type(self, product: Product) -> str | None:
        return get_stock_alert_type(
            product.stock_current,
            product.stock_min,
            margin_percent=self.settings.STOCK_NEAR_MIN_MARGIN_PERCENT,
            is_active=bool(product.is_active),
        )

    def sync_product_stock(self, product: Product) -> None:
        key = f"stock:{product.id}"
        alert_type = self._stock_alert_type(product)

        if alert_type is None:
            self._resolve(key)
            return

        title, message, data = _stock_content(alert_type, product)
        self._upsert(
            dedup_key=key,
            alert_type=alert_type,
            title=title,
            message=message,
            entity_type=ENTITY_TYPE_PRODUCT,
            entity_id=product.id,
            data=data,
        )

    def sync_all_stock(self) -> dict:
        margin = self.settings.STOCK_NEAR_MIN_MARGIN_PERCENT

        # Solo productos que pueden tener aviso: activos y sin stock, o con
        # mínimo cargado y stock hasta `margin`% por encima.
        query = select(Product).where(Product.is_active.is_(True)).where(
            (Product.stock_current <= 0)
            | (
                (Product.stock_min > 0)
                & (Product.stock_current * 100 <= Product.stock_min * (100 + margin))
            )
        )
        products = list(self.db.scalars(query).all())

        keep_keys: set[str] = set()
        for product in products:
            if self._stock_alert_type(product) is None:
                continue
            keep_keys.add(f"stock:{product.id}")
            self.sync_product_stock(product)

        # Avisos de stock activos cuyo producto ya no califica (se repuso,
        # se dio de baja, se borró).
        stale = [
            n.id
            for n in self.repo.list_active_by_category("stock")
            if n.dedup_key not in keep_keys
        ]
        resolved = self.repo.resolve_ids(stale, datetime.now(timezone.utc))
        return {"active": len(keep_keys), "resolved": resolved}

    # -- cheques -------------------------------------------------------

    def _check_alert_type(self, check: Check, today: date) -> str | None:
        return get_check_alert_type(
            status=check.status,
            payment_date=check.payment_date,
            due_date=check.due_date,
            today=today,
            days_before=self.settings.CHECK_ALERT_DAYS_BEFORE,
        )

    def sync_check(self, check: Check, today: date | None = None) -> None:
        today = today or today_local()
        key = f"check:{check.id}"
        alert_type = self._check_alert_type(check, today)

        if alert_type is None:
            self._resolve(key)
            return

        title, message, data = _check_content(alert_type, check, today)
        self._upsert(
            dedup_key=key,
            alert_type=alert_type,
            title=title,
            message=message,
            entity_type=ENTITY_TYPE_CHECK,
            entity_id=check.id,
            data=data,
        )

    def notify_check_rejected(self, check: Check) -> None:
        """Aviso puntual: el cheque rebotó. Además cierra el aviso de
        vencimiento que tuviera."""
        self._resolve(f"check:{check.id}")

        who = _check_counterparty(check)
        received = check.direction == "received"
        origin = f"de {who}" if received else f"emitido a {who}"
        self._upsert(
            dedup_key=f"check_rejected:{check.id}",
            alert_type="check_rejected",
            title="Cheque rechazado",
            message=(
                f"El cheque #{check.check_number} {origin} por "
                f"{format_ars(check.amount)} fue rechazado."
            ),
            entity_type=ENTITY_TYPE_CHECK,
            entity_id=check.id,
            data=_check_data(check, who),
        )

    def sync_all_checks(self, today: date | None = None) -> dict:
        today = today or today_local()

        query = (
            select(Check)
            .options(selectinload(Check.client), selectinload(Check.supplier))
            .where(Check.status == "pendiente")
        )
        checks = list(self.db.scalars(query).all())

        keep_keys: set[str] = set()
        for check in checks:
            if self._check_alert_type(check, today) is None:
                continue
            keep_keys.add(f"check:{check.id}")
            self.sync_check(check, today)

        # Avisos de vencimiento activos de cheques que ya no califican
        # (acreditados, depositados, rechazados, borrados). Los de tipo
        # evento (rechazado) no se tocan acá.
        stale = [
            n.id
            for n in self.repo.list_active_by_category("check")
            if n.type not in EVENT_NOTIFICATION_TYPES and n.dedup_key not in keep_keys
        ]
        resolved = self.repo.resolve_ids(stale, datetime.now(timezone.utc))
        return {"active": len(keep_keys), "resolved": resolved}

    # -- mantenimiento -------------------------------------------------

    def archive_and_purge(self) -> dict:
        now = datetime.now(timezone.utc)
        archived = self.repo.resolve_stale_events(
            EVENT_NOTIFICATION_TYPES,
            older_than=now - timedelta(days=EVENT_ARCHIVE_DAYS),
            now=now,
        )
        purged = self.repo.purge_resolved_before(
            now - timedelta(days=self.settings.NOTIFICATIONS_RETENTION_DAYS)
        )
        return {"archived": archived, "purged": purged}

    def run_full_sync(self) -> dict:
        """Barrido completo (lo usa el scheduler)."""
        result = {
            "stock": self.sync_all_stock(),
            "checks": self.sync_all_checks(),
            "maintenance": self.archive_and_purge(),
        }
        return result

    # -- variantes seguras para engancharse en flujos de negocio -------
    #
    # Un aviso nunca debe romper una venta o el alta de un cheque: corren
    # dentro de un SAVEPOINT y cualquier error se loguea y se descarta (el
    # barrido diario lo corrige después).

    def _safe(self, fn, *args) -> None:
        try:
            with self.db.begin_nested():
                fn(*args)
        except Exception:
            logger.exception("No se pudo actualizar la notificación (%s)", fn.__name__)

    def safe_sync_product_stock(self, product: Product) -> None:
        self._safe(self.sync_product_stock, product)

    def safe_sync_check(self, check: Check) -> None:
        self._safe(self.sync_check, check)

    def safe_notify_check_rejected(self, check: Check) -> None:
        self._safe(self.notify_check_rejected, check)
