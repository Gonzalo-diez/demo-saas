from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field

# ---------------- Proveedores (hojas tipo Nico/Ariel/Guillermo) ----------------

class SupplierImportRow(BaseModel):
    row_number: int
    product_name: str
    quantity: int
    unit_cost: Decimal
    # Columna "document" del Excel; si la celda está vacía se usa el tipo por defecto del import.
    document_type: Literal["purchase_invoice", "purchase_quote"] = "purchase_invoice"

class SupplierImportRowError(BaseModel):
    row_number: int
    errors: list[str]

class SupplierImportResult(BaseModel):
    dry_run: bool
    sheet_name: str
    total_rows_read: int
    rows_to_import: list[SupplierImportRow]
    rows_with_errors: list[SupplierImportRowError]
    total_amount: Decimal
    document_type: Literal["purchase_invoice", "purchase_quote"] = "purchase_invoice"
    purchase_invoice_id: int | None = None
    purchase_quote_id: int | None = None

# ---------------- Clientes (hoja Registro Clientes) ----------------

class ClientImportRow(BaseModel):
    row_number: int
    client_name: str
    matched_client_id: int | None
    product_name: str
    quantity: int
    sale_date: date
    amount: Decimal
    payment_method_raw: str | None
    is_paid: bool
    sales_rep_id: int | None = None
    sales_rep_name: str | None = None
    document_type: Literal["sales_invoice", "sales_quote"] = "sales_invoice"

class ClientImportRowError(BaseModel):
    row_number: int
    errors: list[str]

class ClientImportPaymentResult(BaseModel):
    row_number: int
    client_name: str
    amount: Decimal
    allocated_amount: Decimal
    unassigned_amount: Decimal
    invoice_numbers: list[str] = Field(default_factory=list)

class ClientImportResult(BaseModel):
    dry_run: bool
    sheet_name: str
    total_rows_read: int
    rows_to_import: list[ClientImportRow]
    rows_with_errors: list[ClientImportRowError]
    payments_applied: list[ClientImportPaymentResult] = Field(default_factory=list)
    document_type: Literal["sales_invoice", "sales_quote"] = "sales_invoice"
    created_sales_invoice_ids: list[int] = Field(default_factory=list)
    created_sales_quote_ids: list[int] = Field(default_factory=list)
    rows_skipped_already_imported: int = 0