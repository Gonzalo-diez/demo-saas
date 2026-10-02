from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class SupplierSnapshot(BaseModel):
    id: int
    name: str
    tax_id: str | None = None

class PurchaseInvoiceItemBase(BaseModel):
    product_id: int | None = Field(default=None, gt=0)
    product_name: str = Field(..., min_length=1, max_length=255)
    product_sku: str | None = Field(default=None, max_length=100)
    quantity: int = Field(..., gt=0)
    unit_cost: Decimal = Field(..., gt=0)
    subtotal: Decimal = Field(..., ge=0)

class PurchaseInvoiceItemCreate(BaseModel):
    product_id: int | None = Field(default=None, gt=0)
    product_name: str = Field(..., min_length=1, max_length=255)
    product_sku: str | None = Field(default=None, max_length=100)
    quantity: int = Field(..., gt=0)
    unit_cost: Decimal = Field(..., gt=0)

class PurchaseInvoiceItemUpdate(BaseModel):
    product_id: int | None = Field(default=None, gt=0)
    product_name: str | None = Field(default=None, min_length=1, max_length=255)
    product_sku: str | None = Field(default=None, max_length=100)
    quantity: int | None = Field(default=None, gt=0)
    unit_cost: Decimal | None = Field(default=None, gt=0)

class PurchaseInvoiceItemResponse(PurchaseInvoiceItemBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class PurchaseInvoiceBase(BaseModel):
    supplier_id: int | None = None
    supplier_name: str = Field(..., min_length=1, max_length=255)
    supplier_tax_id: str | None = Field(default=None, max_length=50)
    supplier_snapshot: SupplierSnapshot | None = None
    invoice_number: str = Field(..., min_length=1, max_length=100)
    invoice_date: date
    status: str = Field(default="draft", min_length=1, max_length=50)
    notes: str | None = Field(default=None, max_length=1000)
    total_amount: Decimal | None = Field(default=None, ge=0)

class PurchaseInvoiceCreate(BaseModel):
    supplier_id: int | None = None
    supplier_name: str
    supplier_tax_id: str | None = Field(default=None, max_length=50)
    invoice_number: str = Field(..., min_length=1, max_length=100)
    invoice_date: date
    notes: str | None = Field(default=None, max_length=1000)
    items: list[PurchaseInvoiceItemCreate] = Field(..., min_length=1)
    force: bool = Field(
        default=False,
        description=(
            "Si es False (default) y ya existe un remito activo del mismo "
            "proveedor, misma fecha y mismos productos/cantidades, se "
            "rechaza como posible duplicado. Pasar True para crearlo igual."
        ),
    )

class PurchaseInvoiceUpdate(BaseModel):
    supplier_id: int | None = None
    supplier_name: str | None = Field(default=None, min_length=1, max_length=255)
    supplier_tax_id: str | None = Field(default=None, max_length=50)
    invoice_number: str | None = Field(default=None, min_length=1, max_length=100)
    invoice_date: date | None = None
    notes: str | None = Field(default=None, max_length=1000)

class PurchaseInvoiceUpdateStatus(BaseModel):
    status: str = Field(..., min_length=1, max_length=50)

class PurchaseInvoiceCreatorSummary(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)

class PurchaseInvoiceResponse(PurchaseInvoiceBase):
    id: int
    supplier_id: int | None = None
    payment_status: str
    paid_amount: Decimal
    created_by: int | None = None
    created_at: datetime
    creator: PurchaseInvoiceCreatorSummary | None = None
    items: list[PurchaseInvoiceItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class PurchaseInvoiceListResponse(BaseModel):
    purchase_invoices: list[PurchaseInvoiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    
class PurchaseInvoiceLinkProduct(BaseModel):
    product_id: int = Field(..., gt=0)