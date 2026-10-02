from fastapi import APIRouter, Depends, Query, status, UploadFile, File, Form, Request
from fastapi.responses import Response
from typing import Annotated
from sqlalchemy.orm import Session
from app.core.rate_limit import limiter
from app.db.base import get_db, get_db_with_commit
from app.core.dependencies import get_current_active_user
from app.schemas.invoice_import_schema import (
    PurchaseInvoiceImportPreviewResponse, 
    PurchaseInvoiceImportCommitRequest
)
from app.services.invoice_import_service import InvoiceImportService
from app.models.sales_rep_model import SalesRep
from app.schemas.purchase_invoice_schema import (
    PurchaseInvoiceCreate,
    PurchaseInvoiceItemResponse,
    PurchaseInvoiceLinkProduct,
    PurchaseInvoiceListResponse,
    PurchaseInvoiceResponse,
    PurchaseInvoiceUpdate,
    PurchaseInvoiceUpdateStatus,
)
from app.services.purchase_invoice_service import PurchaseInvoiceService
from app.services.purchase_invoice_pdf_service import build_purchase_invoice_pdf

router = APIRouter(prefix="/purchase-invoices", tags=["purchase-invoices"])

@router.get("", response_model=PurchaseInvoiceListResponse)
@limiter.limit("30/minute")
def get_purchase_invoices(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = PurchaseInvoiceService(db)
    return service.get_purchase_invoices(
        page=page,
        page_size=page_size,
        status_value=status,
    )

@router.get("/{purchase_invoice_id}", response_model=PurchaseInvoiceResponse)
def get_purchase_invoice(
    purchase_invoice_id: int,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = PurchaseInvoiceService(db)
    return service.get_by_id(purchase_invoice_id)

@router.get("/{purchase_invoice_id}/download-pdf")
@limiter.limit("10/minute")
def download_purchase_invoice_pdf(
    request: Request,
    purchase_invoice_id: int,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = PurchaseInvoiceService(db)
    invoice = service.get_by_id(purchase_invoice_id)
    pdf_bytes = build_purchase_invoice_pdf(invoice)
    filename = f"remito-compra-{invoice.invoice_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@router.post(
    "",
    response_model=PurchaseInvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute")
def create_purchase_invoice(
    request: Request,
    data: PurchaseInvoiceCreate,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = PurchaseInvoiceService(db)
    return service.create(data, current_user)

@router.put("/{purchase_invoice_id}", response_model=PurchaseInvoiceResponse)
@limiter.limit("5/minute")
def update_purchase_invoice(
    request: Request,
    purchase_invoice_id: int,
    data: PurchaseInvoiceUpdate,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    service = PurchaseInvoiceService(db)
    return service.update(purchase_invoice_id, data)

@router.patch(
    "/{purchase_invoice_id}/items/{item_id}/link-product",
    response_model=PurchaseInvoiceItemResponse,
)
@limiter.limit("5/minute")
def link_purchase_invoice_item_to_product(
    request: Request,
    purchase_invoice_id: int,
    item_id: int,
    data: PurchaseInvoiceLinkProduct,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    service = PurchaseInvoiceService(db)
    return service.link_item_to_product(purchase_invoice_id, item_id, data)

@router.patch("/{purchase_invoice_id}/status", response_model=PurchaseInvoiceResponse)
@limiter.limit("5/minute")
def update_purchase_invoice_status(
    request: Request,
    purchase_invoice_id: int,
    data: PurchaseInvoiceUpdateStatus,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = PurchaseInvoiceService(db)
    return service.update_status(purchase_invoice_id, data.status, current_user=current_user)

@router.post(
    "/import/preview-file",
    response_model=PurchaseInvoiceImportPreviewResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("5/minute")
async def preview_purchase_invoice_file(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    service = InvoiceImportService(db)
    return await service.preview_purchase_file(file)

@router.post(
    "/import/commit",
    response_model=PurchaseInvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute")
def commit_purchase_invoice_import(
    request: Request,
    data: PurchaseInvoiceImportCommitRequest,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = InvoiceImportService(db)
    return service.commit_purchase(data, current_user)

@router.post(
    "/import/commit-file",
    response_model=PurchaseInvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute")
async def commit_purchase_invoice_file(
    request: Request,
    file: UploadFile = File(...),
    supplier_id: Annotated[int | None, Form()] = None,
    notes: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = InvoiceImportService(db)
    return await service.commit_purchase_file(
        file=file,
        current_user=current_user,
        supplier_id=supplier_id,
        notes=notes,
    )