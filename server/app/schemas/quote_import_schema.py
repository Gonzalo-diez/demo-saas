from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field

class ParsedQuoteItem(BaseModel):
    product_name: str | None = None
    quantity: int | None = None
    unit_cost: Decimal | None = None
    unit_price: Decimal | None = None
    subtotal: Decimal | None = None
    confidence: float | None = None
    warnings: list[str] = Field(default_factory=list)

class QuoteItemCommit(BaseModel):
    product_id: int | None = None
    product_name: str | None = None
    product_sku: str | None = None
    quantity: int
    unit_cost: Decimal | None = None
    unit_price: Decimal | None = None
    is_user_edited: bool = False

class PurchaseQuoteImportPreviewResponse(BaseModel):
    supplier_name: str | None = None
    supplier_tax_id: str | None = None
    quote_number: str | None = None
    quote_date: date | None = None
    total_amount: Decimal | None = None
    items: list[ParsedQuoteItem] = Field(default_factory=list)
    raw_text: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

class PurchaseQuoteImportCommitRequest(BaseModel):
    supplier_id: int | None = None
    supplier_name: str
    supplier_tax_id: str | None = None
    quote_number: str
    quote_date: date
    valid_until: date | None = None
    notes: str | None = None
    items: list[QuoteItemCommit]
    force: bool = False

class SalesQuoteImportPreviewResponse(BaseModel):
    client_name: str | None = None
    client_tax_id: str | None = None
    payment_method: str | None = None
    quote_number: str | None = None
    quote_date: date | None = None
    total_amount: Decimal | None = None
    items: list[ParsedQuoteItem] = Field(default_factory=list)
    raw_text: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

class SalesQuoteImportCommitRequest(BaseModel):
    client_id: int | None = None
    client_name: str | None = None
    client_tax_id: str | None = None
    payment_method: str | None = None
    quote_number: str
    quote_date: date
    valid_until: date | None = None
    notes: str | None = None
    items: list[QuoteItemCommit]
    force: bool = False