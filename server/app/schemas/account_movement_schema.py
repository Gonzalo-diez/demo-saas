from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

# --- Resúmenes anidados ---

class AccountMovementClientSummary(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class AccountMovementSupplierSummary(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class AccountMovementCreatorSummary(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)

class InvoiceReferenceSummary(BaseModel):
    """
    Resumen liviano del remito referenciado por un movimiento
    (reference_type == 'sales_invoice' | 'purchase_invoice'), para no
    obligar a una segunda consulta solo para ver número/fecha/total.
    """
    id: int
    invoice_number: str
    invoice_date: date
    total_amount: Decimal | None = None
    payment_status: str
    # 'sales_invoice' | 'sales_quote' | 'purchase_invoice'. Cuando es un
    # presupuesto, invoice_number / invoice_date llevan quote_number / quote_date.
    document_type: str = "sales_invoice"

    model_config = ConfigDict(from_attributes=True)

class PaymentAllocationSummary(BaseModel):
    """
    Detalle de a qué remito(s) se imputó un movimiento de tipo 'payment'.

    Se usa tanto para movimientos de cliente (ClientPaymentAllocation,
    columna `sales_invoice_id`) como de proveedor (SupplierPaymentAllocation,
    columna `purchase_invoice_id`) — de ahí el AliasChoices, para que
    `model_validate(...)` directo sobre el modelo ORM funcione en los dos
    casos sin importar cuál de las dos columnas tenga el objeto.
    """
    invoice_id: int = Field(
        validation_alias=AliasChoices("invoice_id", "sales_invoice_id", "purchase_invoice_id")
    )
    invoice_number: str | None = None
    amount_applied: Decimal
    # 'sales_invoice' | 'sales_quote' | 'purchase_invoice'. Si es un
    # presupuesto, invoice_id / invoice_number son los del presupuesto.
    document_type: str = "sales_invoice"

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def _resolve_document_from_orm(cls, data):
        """
        Una imputación apunta a un remito O a un presupuesto (la otra columna
        es NULL). Si viene un objeto ORM cuyo documento es un presupuesto,
        tomamos su id/número en vez de fallar por el id de remito en None.
        """
        if isinstance(data, dict):
            return data
        for id_attr, rel_attr, number_attr, doc_type in (
            ("sales_quote_id", "sales_quote", "quote_number", "sales_quote"),
            ("purchase_quote_id", "purchase_quote", "quote_number", "purchase_quote"),
        ):
            doc_id = getattr(data, id_attr, None)
            if doc_id is not None:
                doc = getattr(data, rel_attr, None)
                return {
                    "invoice_id": doc_id,
                    "invoice_number": getattr(doc, number_attr, None) if doc else None,
                    "amount_applied": data.amount_applied,
                    "document_type": doc_type,
                }
        return data

# --- Asignación de pagos (input) ---

class PaymentAllocationItem(BaseModel):
    invoice_id: int = Field(..., gt=0)
    amount: Decimal = Field(..., gt=0)

class ClientPaymentAllocationItem(PaymentAllocationItem):
    """
    Imputación de un cobro de cliente. `invoice_id` es el id del documento
    (se mantiene el nombre por compatibilidad con el front); `document_type`
    dice si es un remito de venta o un presupuesto de venta de pedido.
    """
    document_type: Literal["sales_invoice", "sales_quote"] = "sales_invoice"

# --- Cliente ---

class ClientAccountMovementResponse(BaseModel):
    id: int
    client_id: int
    movement_type: str
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    reference_type: str | None = None
    reference_id: int | None = None
    payment_method: str | None = None
    notes: str | None = None
    created_by: int | None = None
    created_at: datetime

    client: AccountMovementClientSummary | None = None
    creator: AccountMovementCreatorSummary | None = None

    # Enriquecimiento: se completa en el service, no viene directo del modelo
    reference_summary: InvoiceReferenceSummary | None = None
    allocations: list[PaymentAllocationSummary] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class ClientAccountMovementListResponse(BaseModel):
    items: list[ClientAccountMovementResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class ClientPaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Monto del cobro, siempre positivo")
    payment_method: str = Field(..., min_length=1, max_length=30)
    notes: str | None = Field(default=None, max_length=1000)
    # Opcional: a qué remito(s) puntuales se imputa este cobro.
    # Si se omite, el cobro queda "a cuenta" del saldo general del cliente,
    # sin afectar el payment_status de ningún remito en particular.
    allocations: list[ClientPaymentAllocationItem] | None = None

    @model_validator(mode="after")
    def validate_allocations_sum(self):
        if self.allocations:
            total_allocated = sum(a.amount for a in self.allocations)
            if total_allocated > self.amount:
                raise ValueError(
                    "La suma de las asignaciones no puede superar el monto del cobro"
                )
        return self

# --- Proveedor ---

class SupplierAccountMovementResponse(BaseModel):
    id: int
    supplier_id: int
    movement_type: str
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    reference_type: str | None = None
    reference_id: int | None = None
    payment_method: str | None = None
    notes: str | None = None
    created_by: int | None = None
    created_at: datetime

    supplier: AccountMovementSupplierSummary | None = None
    creator: AccountMovementCreatorSummary | None = None

    reference_summary: InvoiceReferenceSummary | None = None
    allocations: list[PaymentAllocationSummary] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class SupplierAccountMovementListResponse(BaseModel):
    items: list[SupplierAccountMovementResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class SupplierPaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Monto del pago, siempre positivo")
    payment_method: str = Field(..., min_length=1, max_length=30)
    notes: str | None = Field(default=None, max_length=1000)
    allocations: list[PaymentAllocationItem] | None = None

    @model_validator(mode="after")
    def validate_allocations_sum(self):
        if self.allocations:
            total_allocated = sum(a.amount for a in self.allocations)
            if total_allocated > self.amount:
                raise ValueError(
                    "La suma de las asignaciones no puede superar el monto del pago"
                )
        return self

# --- Pagos de remitos ONLINE (sin cuenta corriente) ---

class SalesInvoicePaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    payment_method: str = Field(..., min_length=1, max_length=30)
    notes: str | None = Field(default=None, max_length=1000)

class SalesInvoicePaymentResponse(BaseModel):
    id: int
    sales_invoice_id: int
    amount: Decimal
    payment_method: str
    notes: str | None = None
    created_by: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SalesInvoicePaymentListResponse(BaseModel):
    payments: list[SalesInvoicePaymentResponse]
    payment_status: str
    paid_amount: Decimal
    total_amount: Decimal | None = None
    
# --- Pagos de presupuestos ONLINE (sin cuenta corriente) ---
    
class SalesQuotePaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    payment_method: str = Field(..., min_length=1, max_length=30)
    notes: str | None = Field(default=None, max_length=1000)


class SalesQuotePaymentResponse(BaseModel):
    id: int
    sales_quote_id: int
    amount: Decimal
    payment_method: str
    notes: str | None = None
    created_by: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SalesQuotePaymentListResponse(BaseModel):
    payments: list[SalesQuotePaymentResponse]
    payment_status: str
    paid_amount: Decimal
    total_amount: Decimal | None = None