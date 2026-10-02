from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class SupplierSnapshot(BaseModel):
    id: int
    name: str
    tax_id: str | None = None

class PurchaseQuoteItemCreate(BaseModel):
    product_id: int | None = Field(default=None, gt=0)

    product_name: str = Field(..., min_length=1, max_length=255)
    product_sku: str | None = Field(default=None, max_length=120)

    quantity: int = Field(..., gt=0)
    unit_cost: Decimal = Field(..., ge=0)

class PurchaseQuoteItemResponse(BaseModel):
    id: int
    product_id: int | None = None
    product_name: str
    product_sku: str | None = None
    quantity: int
    unit_cost: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)

class PurchaseQuoteLinkProduct(BaseModel):
    product_id: int = Field(..., gt=0)

class PurchaseQuoteBase(BaseModel):
    supplier_id: int | None = Field(default=None, gt=0)
    supplier_name: str | None = Field(default=None, max_length=255)
    supplier_tax_id: str | None = Field(default=None, max_length=50)

    quote_number: str = Field(..., min_length=1, max_length=100)
    quote_date: date
    valid_until: date | None = None

    notes: str | None = None

class PurchaseQuoteCreate(PurchaseQuoteBase):
    items: list[PurchaseQuoteItemCreate] = Field(..., min_length=1)
    force: bool = False

class PurchaseQuoteUpdate(BaseModel):
    quote_number: str | None = Field(default=None, min_length=1, max_length=100)
    quote_date: date | None = None
    valid_until: date | None = None
    notes: str | None = None

class PurchaseQuoteUpdateStatus(BaseModel):
    status: str = Field(..., min_length=1, max_length=20)

class PurchaseQuoteCreatorSummary(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)

class PurchaseQuoteResponse(BaseModel):
    id: int
    supplier_id: int | None = None
    supplier_name: str
    supplier_tax_id: str | None = None
    supplier_snapshot: dict | None = None

    quote_number: str
    quote_date: date
    valid_until: date | None = None
    status: str
    notes: str | None = None
    total_amount: Decimal | None = None

    created_by: int | None = None
    creator: PurchaseQuoteCreatorSummary | None = None

    items: list[PurchaseQuoteItemResponse] = Field(default_factory=list)

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PurchaseQuoteListResponse(BaseModel):
    purchase_quotes: list[PurchaseQuoteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int