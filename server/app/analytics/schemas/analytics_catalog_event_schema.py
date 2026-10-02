from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.analytics.constants.event_type_constant import AnalyticsEventType

class AnalyticsCatalogEventBase(BaseModel):
    visitor_id: str = Field(..., min_length=1, max_length=128)
    session_id: str = Field(..., min_length=1, max_length=128)
    event_type: AnalyticsEventType = Field(...)

    product_id: Optional[int] = Field(default=None, gt=0)
    sales_rep_id: Optional[int] = Field(default=None, gt=0)

    zone_h3_index: Optional[str] = Field(default=None, max_length=32)
    source: Optional[str] = Field(default=None, max_length=64)

    metadata_json: Optional[dict[str, Any]] = None

class AnalyticsCatalogEventCreate(AnalyticsCatalogEventBase):
    """
    Payload para registrar un evento del catálogo.
    """
    pass


class AnalyticsCatalogEventUpdate(BaseModel):
    event_type: Optional[str] = Field(default=None, min_length=1, max_length=64)

    product_id: Optional[int] = Field(default=None, gt=0)
    sales_rep_id: Optional[int] = Field(default=None, gt=0)

    zone_h3_index: Optional[str] = Field(default=None, max_length=32)
    source: Optional[str] = Field(default=None, max_length=64)

    metadata_json: Optional[dict[str, Any]] = None

class AnalyticsCatalogEventRead(AnalyticsCatalogEventBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)