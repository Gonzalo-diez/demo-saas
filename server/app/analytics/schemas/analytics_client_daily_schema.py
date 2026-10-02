from datetime import date, datetime
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, ConfigDict

class ProductBoughtEntry(BaseModel):
    """Entrada individual del JSONB products_bought."""
    product_id: int
    qty: int
    amount: Decimal
    product_name: str | None = None
    category: str | None = None
    brand: str | None = None

class CategorySummaryEntry(BaseModel):
    """Resumen agregado por categoría dentro de un cliente."""
    category: str
    qty: int
    amount: Decimal
    unique_products: int

class AnalyticsClientDailyBase(BaseModel):
    date: date
    client_id: int

    total_orders: int = 0
    revenue_generated: Decimal = Decimal("0")
    cost_generated: Decimal = Decimal("0")
    margin_generated: Decimal = Decimal("0")
    products_bought: list[dict[str, Any]] = []
    unique_products_count: int = 0
    categories_summary: list[dict[str, Any]] = []

class AnalyticsClientDailyCreate(AnalyticsClientDailyBase):
    pass

class AnalyticsClientDailyRead(AnalyticsClientDailyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime