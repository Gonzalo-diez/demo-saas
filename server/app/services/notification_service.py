import math

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.constants.notifications_constant import (
    ALLOWED_NOTIFICATION_TYPES,
    NOTIFICATION_CATEGORIES,
)
from app.models.notification_model import Notification
from app.repositories.notification_repository import NotificationRepository


class NotificationService:
    """Lo que ve el usuario: listado, contador de no leídas y marcar como leída.
    (Quién/cuándo se genera cada aviso vive en NotificationAlertService.)"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificationRepository(db)

    @staticmethod
    def _to_dict(notification: Notification, is_read: bool) -> dict:
        return {
            "id": notification.id,
            "category": notification.category,
            "type": notification.type,
            "severity": notification.severity,
            "title": notification.title,
            "message": notification.message,
            "entity_type": notification.entity_type,
            "entity_id": notification.entity_id,
            "data": notification.data,
            "is_read": is_read,
            "notified_at": notification.notified_at,
            "resolved_at": notification.resolved_at,
            "created_at": notification.created_at,
        }

    def get_notifications(
        self,
        user_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        type_: str | None = None,
        unread_only: bool = False,
        include_resolved: bool = False,
    ) -> dict:
        if category is not None and category not in NOTIFICATION_CATEGORIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Categoría inválida. Las permitidas son: {', '.join(sorted(NOTIFICATION_CATEGORIES))}",
            )
        if type_ is not None and type_ not in ALLOWED_NOTIFICATION_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de notificación inválido",
            )

        page = max(1, page)
        page_size = max(1, page_size)

        rows, total = self.repo.list_for_user(
            user_id,
            page=page,
            page_size=page_size,
            category=category,
            type_=type_,
            unread_only=unread_only,
            include_resolved=include_resolved,
        )

        unread = self.repo.count_unread_by_category(user_id)

        return {
            "items": [self._to_dict(n, is_read) for n, is_read in rows],
            "total": total,
            "unread_count": sum(unread.values()),
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 1,
        }

    def get_unread_count(self, user_id: int) -> dict:
        by_category = self.repo.count_unread_by_category(user_id)
        return {
            "unread_count": sum(by_category.values()),
            "by_category": by_category,
        }

    def mark_read(self, notification_id: int, user_id: int) -> dict:
        notification = self.repo.get_by_id(notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notificación no encontrada",
            )
        self.repo.mark_read(notification_id, user_id)
        return {"id": notification_id, "is_read": True}

    def mark_all_read(self, user_id: int, category: str | None = None) -> dict:
        if category is not None and category not in NOTIFICATION_CATEGORIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Categoría inválida. Las permitidas son: {', '.join(sorted(NOTIFICATION_CATEGORIES))}",
            )
        marked = self.repo.mark_all_read(user_id, category)
        return {
            "marked": marked,
            "unread_count": self.get_unread_count(user_id)["unread_count"],
        }
