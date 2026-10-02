from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class LedgerPaymentEntry(BaseModel):
    """Una forma de pago aplicada a una operación, con su fecha.

    `id` identifica la asignación de pago (SupplierPaymentAllocation /
    ClientPaymentAllocation) o el pago puntual online (SalesInvoicePayment),
    según la pestaña — se usa para editarlo/borrarlo.
    """
    id: int
    method: str
    amount: Decimal
    date: datetime

class LedgerProductLine(BaseModel):
    product_id: int | None = None
    product_name: str
    quantity: int
    # Solo se completa para clientes/online (stock ACTUAL en tiempo real)
    stock_current: int | None = None

class SalesRepSummary(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

# ---------------- Proveedores ----------------

class SupplierPurchaseRow(BaseModel):
    id: int
    document_type: Literal["purchase_invoice", "purchase_quote"]
    # invoice_number / quote_number son texto (ej. "0001-00000042", "IMP-NICO-...")
    document_number: str | None = None
    purchase_date: date
    supplier_id: int | None = None
    supplier_name: str
    products: list[LedgerProductLine] = Field(default_factory=list)
    total_quantity: int
    total_amount: Decimal | None = None
    payments: list[LedgerPaymentEntry] = Field(default_factory=list)
    paid_amount: Decimal
    balance: Decimal
    payment_status: str

    model_config = ConfigDict(from_attributes=True)

class SupplierPurchasesGroup(BaseModel):
    """Una tabla por sales rep, al estilo de las hojas Nico/Ariel/Guillermo."""
    sales_rep: SalesRepSummary | None = None  # None = compras sin vendedor asignado
    rows: list[SupplierPurchaseRow] = Field(default_factory=list)
    total: int = 0

class SupplierPurchasesLedgerResponse(BaseModel):
    groups: list[SupplierPurchasesGroup] = Field(default_factory=list)

# ---------------- Clientes ----------------

class ClientSaleRow(BaseModel):
    id: int
    document_type: Literal["sales_invoice", "sales_quote"]
    document_number: str | None = None
    sale_date: date
    client_id: int | None = None
    client_name: str
    sales_type: str = "B2B"
    products: list[LedgerProductLine] = Field(default_factory=list)
    total_quantity: int
    total_amount: Decimal | None = None
    payments: list[LedgerPaymentEntry] = Field(default_factory=list)
    paid_amount: Decimal
    balance: Decimal
    payment_status: str

    model_config = ConfigDict(from_attributes=True)

class ClientSalesLedgerResponse(BaseModel):
    items: list[ClientSaleRow]
    total: int
    page: int
    page_size: int
    total_pages: int

class ClientSalesSummaryGroup(BaseModel):
    """Un ítem por sub-pestaña: el vendedor y cuántas ventas de cliente tiene."""
    sales_rep: SalesRepSummary | None = None  # None = ventas sin vendedor asignado
    total: int = 0

class ClientSalesSummaryResponse(BaseModel):
    groups: list[ClientSalesSummaryGroup] = Field(default_factory=list)
    total_all: int = 0

# ---------------- Alta / edición de pagos por fila ----------------

class LedgerPaymentCreateRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    method: str = Field(..., min_length=1, max_length=30)
    date: datetime | None = None
    notes: str | None = Field(default=None, max_length=1000)

class LedgerPaymentUpdateRequest(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0)
    method: str | None = Field(default=None, min_length=1, max_length=30)
    date: datetime | None = None
    notes: str | None = Field(default=None, max_length=1000)