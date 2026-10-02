from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    id: int
    category: Literal["stock", "check"]
    type: str
    severity: Literal["info", "warning", "critical"]
    title: str
    message: str
    entity_type: str | None
    entity_id: int | None
    data: dict[str, Any] | None
    is_read: bool
    notified_at: datetime
    resolved_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int
    total_pages: int


class UnreadCountResponse(BaseModel):
    unread_count: int
    by_category: dict[str, int]


class MarkReadResponse(BaseModel):
    id: int
    is_read: bool


class MarkAllReadResponse(BaseModel):
    marked: int
    unread_count: int
