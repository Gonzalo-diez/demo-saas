from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class AnalyticsDailyBase(BaseModel):
    date: date

    total_orders: int = 0
    total_clients: int = 0
    total_products_sold: int = 0

    revenue_generated: Decimal = Decimal("0")
    cost_generated: Decimal = Decimal("0")
    margin_generated: Decimal = Decimal("0")

    average_ticket: Decimal = Decimal("0")

class AnalyticsDailyCreate(AnalyticsDailyBase):
    pass

class AnalyticsDailyRead(AnalyticsDailyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime