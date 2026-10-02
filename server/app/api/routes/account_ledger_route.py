from datetime import date
from decimal import Decimal
from typing import Literal
from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.core.rate_limit import limiter
from app.db.base import get_db, get_db_with_commit
from app.models.sales_rep_model import SalesRep
from app.schemas.account_ledger_schema import (
    ClientSaleRow,
    ClientSalesLedgerResponse,
    ClientSalesSummaryResponse,
    LedgerPaymentCreateRequest,
    LedgerPaymentUpdateRequest,
    SupplierPurchaseRow,
    SupplierPurchasesLedgerResponse,
)
from app.services.account_ledger_export_service import (
    build_client_sales_pdf,
    build_client_sales_xlsx,
    build_supplier_purchases_pdf,
    build_supplier_purchases_xlsx,
)
from app.services.account_ledger_service import AccountLedgerService

router = APIRouter(prefix="/account-ledger", tags=["account-ledger"])


@router.get("/suppliers", response_model=SupplierPurchasesLedgerResponse)
@limiter.limit("30/minute")
def get_supplier_purchases_ledger(
    request: Request,
    sales_rep_id: int | None = Query(default=None, gt=0),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    """
    Compras a proveedores agrupadas por sales rep, una tabla por
    vendedor (estilo hojas Nico / Ariel / Guillermo del Excel).
    """
    service = AccountLedgerService(db)
    return service.get_supplier_purchases_ledger(
        sales_rep_id=sales_rep_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/clients/summary", response_model=ClientSalesSummaryResponse)
@limiter.limit("30/minute")
def get_client_sales_summary(
    request: Request,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    """
    Cantidad de ventas de cliente por vendedor, para las sub-pestañas
    (una por vendedor, como en Proveedores).
    """
    service = AccountLedgerService(db)
    return service.get_client_sales_summary(date_from=date_from, date_to=date_to)


@router.get("/clients", response_model=ClientSalesLedgerResponse)
@limiter.limit("30/minute")
def get_client_sales_ledger(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    client_id: int | None = Query(default=None, gt=0),
    sales_rep_id: int | None = Query(default=None, gt=0),
    unassigned: bool = Query(default=False),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    """
    Ventas a clientes (B2B y ONLINE): fecha, cliente, productos/cantidad,
    stock actual, formas de pago con fecha.
    """
    service = AccountLedgerService(db)
    return service.get_client_sales_ledger(
        page=page,
        page_size=page_size,
        client_id=client_id,
        sales_rep_id=sales_rep_id,
        only_unassigned=unassigned,
        date_from=date_from,
        date_to=date_to,
    )


# ---------------------------------------------------------------------
# Proveedores: alta / edición / borrado de pagos por fila
# ---------------------------------------------------------------------

@router.post(
    "/suppliers/purchases/{purchase_invoice_id}/payments/{document_type}",
    response_model=SupplierPurchaseRow,
    status_code=201,
)
@limiter.limit("30/minute")
def add_supplier_payment(
    request: Request,
    document_type: Literal["purchase_invoice", "purchase_quote"],
    purchase_invoice_id: int,
    data: LedgerPaymentCreateRequest,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = AccountLedgerService(db)
    row = service.add_supplier_payment(
        document_type=document_type,
        document_id=purchase_invoice_id,
        amount=data.amount,
        method=data.method,
        payment_date=data.date,
        notes=data.notes,
        current_user=current_user,
    )
    return row


@router.patch("/suppliers/payments/{allocation_id}", response_model=SupplierPurchaseRow)
@limiter.limit("30/minute")
def edit_supplier_payment(
    request: Request,
    allocation_id: int,
    data: LedgerPaymentUpdateRequest,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    service = AccountLedgerService(db)
    row = service.edit_supplier_payment(
        allocation_id=allocation_id,
        amount=data.amount,
        method=data.method,
        payment_date=data.date,
        notes=data.notes,
    )
    return row


@router.delete("/suppliers/payments/{allocation_id}", response_model=SupplierPurchaseRow)
@limiter.limit("30/minute")
def delete_supplier_payment(
    request: Request,
    allocation_id: int,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    service = AccountLedgerService(db)
    row = service.delete_supplier_payment(allocation_id)
    return row


# ---------------------------------------------------------------------
# Clientes: alta / edición / borrado de pagos por fila
# ---------------------------------------------------------------------

@router.post(
    "/clients/sales/{sales_invoice_id}/payments/{document_type}",
    response_model=ClientSaleRow,
    status_code=201,
)
@limiter.limit("30/minute")
def add_client_payment(
    request: Request,
    document_type: Literal["sales_invoice", "sales_quote"],
    sales_invoice_id: int,
    data: LedgerPaymentCreateRequest,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = AccountLedgerService(db)
    row = service.add_client_payment(
        document_type=document_type,
        document_id=sales_invoice_id,
        amount=data.amount,
        method=data.method,
        payment_date=data.date,
        notes=data.notes,
        current_user=current_user,
    )
    return row


@router.patch("/clients/payments/{allocation_id}", response_model=ClientSaleRow)
@limiter.limit("30/minute")
def edit_client_payment(
    request: Request,
    allocation_id: int,
    data: LedgerPaymentUpdateRequest,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    service = AccountLedgerService(db)
    row = service.edit_client_payment(
        allocation_id=allocation_id,
        amount=data.amount,
        method=data.method,
        payment_date=data.date,
        notes=data.notes,
    )
    return row


@router.delete("/clients/payments/{allocation_id}", response_model=ClientSaleRow)
@limiter.limit("30/minute")
def delete_client_payment(
    request: Request,
    allocation_id: int,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    service = AccountLedgerService(db)
    row = service.delete_client_payment(allocation_id)
    return row


# ---------------------------------------------------------------------
# Exportación a Excel / PDF
# ---------------------------------------------------------------------

_EXPORT_MEDIA_TYPES = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
}


def _export_response(file_bytes: bytes, filename: str, fmt: str) -> Response:
    return Response(
        content=file_bytes,
        media_type=_EXPORT_MEDIA_TYPES[fmt],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/suppliers/export")
@limiter.limit("10/minute")
def export_supplier_purchases(
    request: Request,
    format: str = Query(..., pattern="^(xlsx|pdf)$"),
    sales_rep_id: int | None = Query(default=None, gt=0),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = AccountLedgerService(db)
    data = service.get_supplier_purchases_ledger(
        sales_rep_id=sales_rep_id, date_from=date_from, date_to=date_to
    )

    if format == "xlsx":
        file_bytes = build_supplier_purchases_xlsx(data)
        filename = "cuenta-corriente-proveedores.xlsx"
    else:
        file_bytes = build_supplier_purchases_pdf(data)
        filename = "cuenta-corriente-proveedores.pdf"

    return _export_response(file_bytes, filename, format)


@router.get("/clients/export")
@limiter.limit("10/minute")
def export_client_sales(
    request: Request,
    format: str = Query(..., pattern="^(xlsx|pdf)$"),
    client_id: int | None = Query(default=None, gt=0),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = AccountLedgerService(db)
    data = service.get_client_sales_ledger(
        page=1,
        page_size=100000,
        client_id=client_id,
        date_from=date_from,
        date_to=date_to,
    )

    if format == "xlsx":
        file_bytes = build_client_sales_xlsx(data.items)
        filename = "cuenta-corriente-clientes.xlsx"
    else:
        file_bytes = build_client_sales_pdf(data.items)
        filename = "cuenta-corriente-clientes.pdf"

    return _export_response(file_bytes, filename, format)