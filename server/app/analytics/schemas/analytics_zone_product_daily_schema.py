from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class AnalyticsZoneProductDailyBase(BaseModel):
    date: date
    h3_index: str
    product_id: int

    quantity_sold: int = 0
    total_orders: int = 0
    revenue_generated: Decimal = Decimal("0")
    cost_generated: Decimal = Decimal("0")
    margin_generated: Decimal = Decimal("0")
    unique_clients: int = 0

class AnalyticsZoneProductDailyCreate(AnalyticsZoneProductDailyBase):
    pass

class AnalyticsZoneProductDailyRead(AnalyticsZoneProductDailyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime