from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field

class ParsedInvoiceItem(BaseModel):
    product_name: str | None = None
    quantity: int | None = None
    unit_cost: Decimal | None = None
    unit_price: Decimal | None = None
    subtotal: Decimal | None = None
    confidence: float | None = None
    warnings: list[str] = Field(default_factory=list)

class InvoiceItemCommit(BaseModel):
    product_id: int | None = None
    product_name: str | None = None
    product_sku: str | None = None
    quantity: int
    unit_cost: Decimal | None = None
    unit_price: Decimal | None = None
    is_user_edited: bool = False

class PurchaseInvoiceImportPreviewResponse(BaseModel):
    supplier_name: str | None = None
    supplier_tax_id: str | None = None
    invoice_number: str | None = None
    invoice_date: date | None = None
    total_amount: Decimal | None = None
    items: list[ParsedInvoiceItem] = Field(default_factory=list)
    raw_text: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

class PurchaseInvoiceImportCommitRequest(BaseModel):
    supplier_name: str
    supplier_tax_id: str | None = None
    invoice_number: str
    invoice_date: date
    notes: str | None = None
    items: list[InvoiceItemCommit]
    force: bool = False

class SalesInvoiceImportPreviewResponse(BaseModel):
    client_name: str | None = None
    client_tax_id: str | None = None
    invoice_number: str | None = None
    invoice_date: date | None = None
    total_amount: Decimal | None = None
    items: list[ParsedInvoiceItem] = Field(default_factory=list)
    raw_text: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

class SalesInvoiceImportCommitRequest(BaseModel):
    client_id: int | None = None
    client_branch_id: int | None = None
    client_name: str | None = None
    client_tax_id: str | None = None
    invoice_number: str
    invoice_date: date
    notes: str | None = None
    items: list[InvoiceItemCommit]
    force: bool = False