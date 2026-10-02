from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.db.base import get_db, get_db_with_commit
from app.models.sales_rep_model import SalesRep
from app.schemas.notification_schema import (
    MarkAllReadResponse,
    MarkReadResponse,
    NotificationListResponse,
    UnreadCountResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = Query(default=None, description="stock | check"),
    type: str | None = Query(default=None, description="Ej: stock_out, stock_low, check_overdue"),
    unread_only: bool = Query(default=False),
    include_resolved: bool = Query(
        default=False,
        description="Incluye avisos cuya condición ya se resolvió (historial)",
    ),
    db: Session = Depends(get_db),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = NotificationService(db)
    return service.get_notifications(
        current_user.id,
        page=page,
        page_size=page_size,
        category=category,
        type_=type,
        unread_only=unread_only,
        include_resolved=include_resolved,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: SalesRep = Depends(get_current_active_user),
):
    """Para el numerito de la campanita."""
    service = NotificationService(db)
    return service.get_unread_count(current_user.id)


@router.post("/read-all", response_model=MarkAllReadResponse)
def mark_all_read(
    category: str | None = Query(default=None, description="stock | check (si se omite, todas)"),
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = NotificationService(db)
    return service.mark_all_read(current_user.id, category)


@router.post("/{notification_id}/read", response_model=MarkReadResponse)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = NotificationService(db)
    return service.mark_read(notification_id, current_user.id)
