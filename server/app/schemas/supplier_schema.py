from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class SupplierBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    tax_id: str | None = Field(default=None, min_length=1, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=255)
    is_active: bool = True

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    tax_id: str | None = Field(default=None, min_length=1, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None

class SupplierResponse(SupplierBase):
    id: int
    current_balance: Decimal = Decimal("0.00")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
    
class SupplierListResponse(BaseModel):
    suppliers: list[SupplierResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    model_config = ConfigDict(from_attributes=True)