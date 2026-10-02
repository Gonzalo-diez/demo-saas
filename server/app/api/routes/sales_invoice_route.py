from fastapi import APIRouter, Depends, Query, status, UploadFile, File, Form, Request
from fastapi.responses import Response
from typing import Annotated
from sqlalchemy.orm import Session
from app.core.rate_limit import limiter
from app.db.base import get_db, get_db_with_commit
from app.core.dependencies import get_current_active_user
from app.schemas.invoice_import_schema import (
    SalesInvoiceImportPreviewResponse,
    SalesInvoiceImportCommitRequest
)
from app.services.invoice_import_service import InvoiceImportService 
from app.models.sales_rep_model import SalesRep
from app.schemas.account_movement_schema import (
    SalesInvoicePaymentCreate,
    SalesInvoicePaymentListResponse,
)
from app.schemas.sales_invoice_schema import (
    SalesInvoiceCreate,
    SalesInvoiceListResponse,
    SalesInvoiceResponse,
    SalesInvoiceUpdate,
    SalesInvoiceUpdateStatus,
)
from app.services.sales_invoice_service import SalesInvoiceService
from app.services.sales_invoice_pdf_service import build_sales_invoice_pdf

router = APIRouter(prefix="/sales-invoices", tags=["sales-invoices"])

@router.get("", response_model=SalesInvoiceListResponse)
@limiter.limit("30/minute")
def get_sales_invoices(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = SalesInvoiceService(db)
    return service.get_sales_invoices(
        page=page,
        page_size=page_size,
        status_value=status,
    )

@router.get("/{sales_invoice_id}", response_model=SalesInvoiceResponse)
def get_sales_invoice(
    sales_invoice_id: int,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = SalesInvoiceService(db)
    return service.get_by_id(sales_invoice_id)

@router.get("/{sales_invoice_id}/download-pdf")
@limiter.limit("10/minute")
def download_sales_invoice_pdf(
    request: Request,
    sales_invoice_id: int,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = SalesInvoiceService(db)
    invoice = service.get_by_id(sales_invoice_id)
    pdf_bytes = build_sales_invoice_pdf(invoice)
    filename = f"remito-venta-{invoice.invoice_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@router.post(
    "",
    response_model=SalesInvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute")
def create_sales_invoice(
    request: Request,
    data: SalesInvoiceCreate,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = SalesInvoiceService(db)
    return service.create(data, current_user)

@router.put("/{sales_invoice_id}", response_model=SalesInvoiceResponse)
@limiter.limit("5/minute")
def update_sales_invoice(
    request: Request,
    sales_invoice_id: int,
    data: SalesInvoiceUpdate,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    service = SalesInvoiceService(db)
    return service.update(sales_invoice_id, data)

@router.patch("/{sales_invoice_id}/status", response_model=SalesInvoiceResponse)
@limiter.limit("5/minute")
def update_sales_invoice_status(
    request: Request,
    sales_invoice_id: int,
    data: SalesInvoiceUpdateStatus,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = SalesInvoiceService(db)
    return service.update_status(sales_invoice_id, data.status, current_user=current_user)

@router.post(
    "/{sales_invoice_id}/payments",
    response_model=SalesInvoicePaymentListResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("15/minute")
def register_sales_invoice_payment(
    request: Request,
    sales_invoice_id: int,
    data: SalesInvoicePaymentCreate,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    """
    Registra un cobro sobre un remito ONLINE puntual (contra entrega:
    efectivo, Mercado Pago, transferencia, etc). No aplica a remitos con
    cliente de cuenta corriente — para esas usá /client-account-movements.
    """
    service = SalesInvoiceService(db)
    return service.register_online_payment(sales_invoice_id, data, current_user)

@router.get(
    "/{sales_invoice_id}/payments",
    response_model=SalesInvoicePaymentListResponse,
)
def get_sales_invoice_payments(
    sales_invoice_id: int,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = SalesInvoiceService(db)
    return service.get_online_payments(sales_invoice_id)

@router.post(
    "/import/preview-file",
    response_model=SalesInvoiceImportPreviewResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("5/minute")
async def preview_sales_invoice_file(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    service = InvoiceImportService(db)
    return await service.preview_sales_file(file)

@router.post(
    "/import/commit",
    response_model=SalesInvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute")
def commit_sales_invoice_import(
    request: Request,
    data: SalesInvoiceImportCommitRequest,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = InvoiceImportService(db)
    return service.commit_sales(data, current_user)

@router.post(
    "/import/commit-file",
    response_model=SalesInvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute")
async def commit_sales_invoice_file(
    request: Request,
    file: UploadFile = File(...),
    client_id: Annotated[int | None, Form()] = None,
    client_branch_id: Annotated[int | None, Form()] = None,
    notes: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = InvoiceImportService(db)
    return await service.commit_sales_file(
        file=file,
        current_user=current_user,
        client_id=client_id,
        client_branch_id=client_branch_id,
        notes=notes,
    )