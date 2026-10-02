from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class InventoryMovementProductSummary(BaseModel):
    id: int
    sku: str | None = None
    name: str

    model_config = ConfigDict(from_attributes=True)

class InventoryMovementCreatorSummary(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)

class InventoryMovementResponse(BaseModel):
    id: int
    product_id: int
    movement_type: str
    quantity: int
    stock_before: int
    stock_after: int
    unit_cost: Decimal | None = None
    unit_price: Decimal | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    notes: str | None = None
    created_by: int | None = None
    created_at: datetime

    product: InventoryMovementProductSummary | None = None
    creator: InventoryMovementCreatorSummary | None = None

    model_config = ConfigDict(from_attributes=True)

class InventoryMovementListResponse(BaseModel):
    items: list[InventoryMovementResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class InventoryMovementFilters(BaseModel):
    product_id: int | None = Field(default=None, gt=0)
    movement_type: str | None = Field(default=None, min_length=1, max_length=50)
    reference_type: str | None = Field(default=None, min_length=1, max_length=50)