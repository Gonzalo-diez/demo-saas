from datetime import datetime
from typing import Optional

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.orm import Session

from app.models.notification_model import Notification, NotificationRead


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Motor de avisos (alta / actualización / resolución)
    # ------------------------------------------------------------------

    def get_active_by_dedup_key(self, dedup_key: str) -> Optional[Notification]:
        query = (
            select(Notification)
            .where(Notification.dedup_key == dedup_key)
            .where(Notification.resolved_at.is_(None))
        )
        return self.db.scalar(query)

    def list_active_by_category(self, category: str) -> list[Notification]:
        query = (
            select(Notification)
            .where(Notification.category == category)
            .where(Notification.resolved_at.is_(None))
        )
        return list(self.db.scalars(query).all())

    def create(
        self,
        *,
        category: str,
        type_: str,
        severity: str,
        level: int,
        title: str,
        message: str,
        dedup_key: str,
        entity_type: str | None,
        entity_id: int | None,
        data: dict | None,
    ) -> Notification:
        notification = Notification(
            category=category,
            type=type_,
            severity=severity,
            level=level,
            title=title,
            message=message,
            dedup_key=dedup_key,
            entity_type=entity_type,
            entity_id=entity_id,
            data=data,
        )
        self.db.add(notification)
        self.db.flush()
        return notification

    def resolve_by_dedup_key(self, dedup_key: str, now: datetime) -> int:
        """Resuelve (si existe) la notificación activa de esa clave.
        Un único UPDATE, sin leer antes."""
        result = self.db.execute(
            update(Notification)
            .where(Notification.dedup_key == dedup_key)
            .where(Notification.resolved_at.is_(None))
            .values(resolved_at=now)
        )
        return result.rowcount or 0

    def resolve_ids(self, notification_ids: list[int], now: datetime) -> int:
        if not notification_ids:
            return 0
        result = self.db.execute(
            update(Notification)
            .where(Notification.id.in_(notification_ids))
            .where(Notification.resolved_at.is_(None))
            .values(resolved_at=now)
        )
        return result.rowcount or 0

    def clear_reads(self, notification_id: int) -> None:
        self.db.execute(
            delete(NotificationRead).where(
                NotificationRead.notification_id == notification_id
            )
        )

    def resolve_stale_events(self, event_types: set[str], older_than: datetime, now: datetime) -> int:
        result = self.db.execute(
            update(Notification)
            .where(Notification.type.in_(event_types))
            .where(Notification.resolved_at.is_(None))
            .where(Notification.notified_at < older_than)
            .values(resolved_at=now)
        )
        return result.rowcount or 0

    def purge_resolved_before(self, before: datetime) -> int:
        result = self.db.execute(
            delete(Notification)
            .where(Notification.resolved_at.is_not(None))
            .where(Notification.resolved_at < before)
        )
        return result.rowcount or 0

    # ------------------------------------------------------------------
    # Consulta para el usuario
    # ------------------------------------------------------------------

    @staticmethod
    def _read_exists(user_id: int):
        return (
            select(NotificationRead.notification_id)
            .where(NotificationRead.notification_id == Notification.id)
            .where(NotificationRead.sales_rep_id == user_id)
            .exists()
        )

    def list_for_user(
        self,
        user_id: int,
        *,
        page: int,
        page_size: int,
        category: str | None = None,
        type_: str | None = None,
        unread_only: bool = False,
        include_resolved: bool = False,
    ) -> tuple[list[tuple[Notification, bool]], int]:
        read_exists = self._read_exists(user_id)

        filters = []
        if not include_resolved:
            filters.append(Notification.resolved_at.is_(None))
        if category:
            filters.append(Notification.category == category)
        if type_:
            filters.append(Notification.type == type_)
        if unread_only:
            filters.append(~read_exists)

        query = (
            select(Notification, read_exists.label("is_read"))
            .where(*filters)
            .order_by(Notification.notified_at.desc(), Notification.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_query = select(func.count()).select_from(Notification).where(*filters)

        rows = [(row[0], bool(row[1])) for row in self.db.execute(query).all()]
        total = self.db.scalar(count_query) or 0
        return rows, total

    def count_unread_by_category(self, user_id: int) -> dict[str, int]:
        read_exists = self._read_exists(user_id)
        query = (
            select(Notification.category, func.count())
            .where(Notification.resolved_at.is_(None))
            .where(~read_exists)
            .group_by(Notification.category)
        )
        return {category: count for category, count in self.db.execute(query).all()}

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------

    def get_by_id(self, notification_id: int) -> Optional[Notification]:
        return self.db.get(Notification, notification_id)

    def mark_read(self, notification_id: int, user_id: int) -> bool:
        """Devuelve True si la marcó ahora, False si ya estaba leída."""
        existing = self.db.get(NotificationRead, (notification_id, user_id))
        if existing:
            return False
        self.db.add(
            NotificationRead(notification_id=notification_id, sales_rep_id=user_id)
        )
        self.db.flush()
        return True

    def mark_all_read(self, user_id: int, category: str | None = None) -> int:
        read_exists = self._read_exists(user_id)
        query = (
            select(Notification.id)
            .where(Notification.resolved_at.is_(None))
            .where(~read_exists)
        )
        if category:
            query = query.where(Notification.category == category)

        ids = list(self.db.scalars(query).all())
        if not ids:
            return 0

        self.db.execute(
            insert(NotificationRead),
            [{"notification_id": nid, "sales_rep_id": user_id} for nid in ids],
        )
        self.db.flush()
        return len(ids)
