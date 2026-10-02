from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.constants.sales_type_constant import SalesType

class ClientSnapshot(BaseModel):
    id: int
    name: str

class ClientBranchSnapshot(BaseModel):
    id: int
    name: str
    address: str | None = None
    city: str | None = None

class SalesRepSnapshot(BaseModel):
    id: int
    name: str
    email: str | None = None

class SalesInvoiceItemCreate(BaseModel):
    product_id: int | None = Field(default=None, gt=0)
    
    product_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    product_brand: str | None = Field(
        default=None,
        max_length=255,
    )

    product_sku: str | None = Field(
        default=None,
        max_length=120,
    )
    
    quantity: int = Field(..., gt=0)

class SalesInvoiceItemResponse(BaseModel):
    id: int
    product_id: int | None = None
    product_name: str
    product_brand: str | None = None
    product_sku: str | None = None
    quantity: int
    unit_cost: Decimal
    unit_price: Decimal
    subtotal_cost: Decimal
    subtotal: Decimal
    margin_amount: Decimal

    model_config = ConfigDict(from_attributes=True)

class SalesInvoiceClientSummary(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class SalesInvoiceClientBranchSummary(BaseModel):
    id: int
    client_id: int
    name: str
    address: str | None = None
    city: str | None = None

    model_config = ConfigDict(from_attributes=True)

class SalesInvoiceSalesRepSummary(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)

class SalesInvoiceBase(BaseModel):
    order_id: int | None = Field(default=None, gt=0)

    sales_type: SalesType

    client_id: int | None = Field(default=None, gt=0)
    client_branch_id: int | None = Field(default=None, gt=0)
    sales_rep_id: int | None = Field(default=None, gt=0)

    customer_name: str | None = Field(default=None, max_length=255)
    customer_phone: str | None = Field(default=None, max_length=50)
    customer_email: EmailStr | None = None

    delivery_type: str | None = Field(default=None, max_length=20)
    delivery_address: str | None = Field(default=None, max_length=255)
    delivery_city: str | None = Field(default=None, max_length=120)
    delivery_reference: str | None = None

    invoice_number: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    invoice_date: date
    status: str = Field(default="draft", min_length=1, max_length=50)
    notes: str | None = Field(
        default=None,
        max_length=1000,
    )

class SalesInvoiceCreate(SalesInvoiceBase):
    client_snapshot: dict | None = None

    client_branch_snapshot: dict | None = None

    sales_rep_snapshot: dict | None = None

    currency: str = Field(
        default="ARS",
        max_length=10,
    )

    items: list[SalesInvoiceItemCreate] = Field(
        ...,
        min_length=1,
    )

    force: bool = Field(
        default=False,
        description=(
            "Si es False (default) y ya existe un remito activo del mismo "
            "cliente, misma fecha y mismos productos/cantidades, se "
            "rechaza como posible duplicado. Pasar True para crearlo igual."
        ),
    )

class SalesInvoiceUpdate(BaseModel):
    client_branch_id: int | None = Field(default=None, gt=0)

    customer_name: str | None = Field(
        default=None,
        max_length=255,
    )

    customer_phone: str | None = Field(
        default=None,
        max_length=50,
    )

    customer_email: EmailStr | None = None

    delivery_type: str | None = Field(
        default=None,
        max_length=20,
    )

    delivery_address: str | None = Field(
        default=None,
        max_length=255,
    )

    delivery_city: str | None = Field(
        default=None,
        max_length=120,
    )

    delivery_reference: str | None = None

    invoice_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    invoice_date: date | None = None

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )

class SalesInvoiceUpdateStatus(BaseModel):
    status: str = Field(..., min_length=1, max_length=50)

class SalesInvoiceResponse(SalesInvoiceBase):
    id: int

    status: str
    payment_status: str
    paid_amount: Decimal

    total_cost: Decimal
    total_amount: Decimal
    margin_amount: Decimal

    currency: str

    created_at: datetime
    updated_at: datetime

    client: SalesInvoiceClientSummary | None = None
    client_branch: SalesInvoiceClientBranchSummary | None = None
    sales_rep: SalesInvoiceSalesRepSummary | None = None

    client_snapshot: ClientSnapshot | None = None
    client_branch_snapshot: ClientBranchSnapshot | None = None
    sales_rep_snapshot: SalesRepSnapshot | None = None

    pdf_generated_at: datetime | None = None
    email_sent_at: datetime | None = None

    items: list[SalesInvoiceItemResponse] = Field(
        default_factory=list
    )

    model_config = ConfigDict(from_attributes=True)

class SalesInvoiceListResponse(BaseModel):
    sales_invoices: list[SalesInvoiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int