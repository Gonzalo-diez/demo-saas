from datetime import date, datetime
from decimal import Decimal
from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from app.constants.sales_type_constant import SalesType

class ClientSnapshot(BaseModel):
    id: int
    name: str
    tax_id: str | None = None

class ClientBranchSnapshot(BaseModel):
    id: int
    name: str
    address: str | None = None
    city: str | None = None

class SalesRepSnapshot(BaseModel):
    id: int
    name: str
    email: str | None = None

class SalesQuoteItemCreate(BaseModel):
    product_id: int | None = Field(default=None, gt=0)

    product_name: str = Field(..., min_length=1, max_length=255)
    product_sku: str | None = Field(default=None, max_length=120)

    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)

class SalesQuoteItemResponse(BaseModel):
    id: int
    product_id: int | None = None
    product_name: str
    product_brand: str | None = None
    product_sku: str | None = None
    quantity: int
    unit_cost: Decimal | None = None
    unit_price: Decimal
    subtotal_cost: Decimal | None = None
    subtotal: Decimal
    margin_amount: Decimal | None = None

    model_config = ConfigDict(from_attributes=True)

class SalesQuoteLinkProduct(BaseModel):
    product_id: int = Field(..., gt=0)

class SalesQuoteBase(BaseModel):
    client_id: int | None = Field(default=None, gt=0)
    client_branch_id: int | None = Field(default=None, gt=0)
    # Para consumidor final / cliente ocasional sin cuenta registrada.
    # (En la base se guardan como customer_name / customer_tax_id.)
    client_name: str | None = Field(default=None, max_length=255)
    client_tax_id: str | None = Field(default=None, max_length=50)

    sales_rep_id: int | None = Field(default=None, gt=0)

    quote_number: str = Field(..., min_length=1, max_length=100)
    quote_date: date
    valid_until: date | None = None

    payment_method: str | None = Field(default=None, max_length=50)
    notes: str | None = None

class SalesQuoteCreate(SalesQuoteBase):
    items: list[SalesQuoteItemCreate] = Field(..., min_length=1)
    force: bool = False

class SalesQuoteUpdate(BaseModel):
    quote_number: str | None = Field(default=None, min_length=1, max_length=100)
    quote_date: date | None = None
    valid_until: date | None = None
    payment_method: str | None = Field(default=None, max_length=50)
    notes: str | None = None

class SalesQuoteUpdateStatus(BaseModel):
    status: str = Field(..., min_length=1, max_length=20)

class SalesQuoteRepSummary(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)

class SalesQuoteResponse(BaseModel):
    id: int
    # Pedido del que nació (None = presupuesto suelto / cotización).
    order_id: int | None = None
    sales_type: SalesType

    client_id: int | None = None
    client_branch_id: int | None = None
    # El modelo guarda customer_name / customer_tax_id; se exponen con los
    # nombres históricos client_name / client_tax_id para no romper al front.
    client_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("client_name", "customer_name"),
    )
    client_tax_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("client_tax_id", "customer_tax_id"),
    )
    customer_phone: str | None = None
    customer_email: str | None = None

    delivery_type: str | None = None
    delivery_address: str | None = None
    delivery_city: str | None = None
    delivery_reference: str | None = None

    client_snapshot: dict | None = None
    client_branch_snapshot: dict | None = None
    sales_rep_snapshot: dict | None = None

    sales_rep_id: int | None = None
    sales_rep: SalesQuoteRepSummary | None = None

    quote_number: str
    quote_date: date
    valid_until: date | None = None
    status: str
    payment_method: str | None = None
    payment_status: str
    paid_amount: Decimal
    notes: str | None = None

    total_cost: Decimal | None = None
    total_amount: Decimal | None = None
    margin_amount: Decimal | None = None
    currency: str

    pdf_generated_at: datetime | None = None
    email_sent_at: datetime | None = None

    items: list[SalesQuoteItemResponse] = Field(default_factory=list)

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class SalesQuoteListResponse(BaseModel):
    sales_quotes: list[SalesQuoteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
