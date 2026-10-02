from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class AnalyticsSalesRepDailyBase(BaseModel):
    date: date
    sales_rep_id: int

    total_orders: int = 0
    total_clients: int = 0
    total_products_sold: int = 0

    revenue_generated: Decimal = Decimal("0")
    cost_generated: Decimal = Decimal("0")
    margin_generated: Decimal = Decimal("0")

class AnalyticsSalesRepDailyCreate(AnalyticsSalesRepDailyBase):
    pass

class AnalyticsSalesRepDailyRead(AnalyticsSalesRepDailyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime