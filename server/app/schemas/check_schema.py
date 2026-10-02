from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.account_movement_schema import (
    ClientPaymentAllocationItem,
    PaymentAllocationItem,
)

class _CheckCreateBase(BaseModel):
    check_number: str = Field(..., min_length=1, max_length=50)
    bank_name: str | None = Field(default=None, max_length=100)
    drawer_name: str | None = Field(default=None, max_length=255)
    amount: Decimal = Field(..., gt=0)
    issue_date: date
    payment_date: date
    due_date: date
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.payment_date < self.issue_date:
            raise ValueError(
                "La fecha de pago no puede ser anterior a la fecha de emisión"
            )
        if self.due_date < self.payment_date:
            raise ValueError(
                "La fecha de vencimiento no puede ser anterior a la fecha de pago"
            )
        return self


class ReceivedCheckCreate(_CheckCreateBase):
    """Cheque recibido de un cliente, como cobro."""
    allocations: list[ClientPaymentAllocationItem] | None = None

    @model_validator(mode="after")
    def validate_allocations_sum(self):
        if self.allocations:
            total_allocated = sum(a.amount for a in self.allocations)
            if total_allocated > self.amount:
                raise ValueError(
                    "La suma de las asignaciones no puede superar el monto del cheque"
                )
        return self


class IssuedCheckCreate(_CheckCreateBase):
    """Cheque emitido a un proveedor, como pago."""
    allocations: list[PaymentAllocationItem] | None = None

    @model_validator(mode="after")
    def validate_allocations_sum(self):
        if self.allocations:
            total_allocated = sum(a.amount for a in self.allocations)
            if total_allocated > self.amount:
                raise ValueError(
                    "La suma de las asignaciones no puede superar el monto del cheque"
                )
        return self


class CheckRejectRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=1000)


class CheckResponse(BaseModel):
    id: int
    direction: Literal["received", "issued"]
    check_number: str
    bank_name: str | None
    drawer_name: str | None
    amount: Decimal
    issue_date: date
    payment_date: date
    due_date: date
    status: Literal["pendiente", "depositado", "acreditado", "rechazado"]
    client_id: int | None
    supplier_id: int | None
    notes: str | None
    client_account_movement_id: int | None
    supplier_account_movement_id: int | None
    deposited_at: datetime | None
    resolved_at: datetime | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CheckListResponse(BaseModel):
    checks: list[CheckResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DocumentPendingChecksResponse(BaseModel):
    pending_amount: Decimal
    checks: list[CheckResponse]


class CheckPendingSummaryResponse(BaseModel):
    pending_amount: Decimal
    pending_count: int
    checks: list[CheckResponse]