from fastapi import APIRouter, Depends, Query, Request, UploadFile, File, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.core.rate_limit import limiter
from app.db.base import get_db, get_db_with_commit
from app.core.dependencies import get_current_active_user
from app.models.sales_rep_model import SalesRep
from app.schemas.purchase_quote_schema import (
    PurchaseQuoteCreate,
    PurchaseQuoteItemResponse,
    PurchaseQuoteLinkProduct,
    PurchaseQuoteListResponse,
    PurchaseQuoteResponse,
    PurchaseQuoteUpdate,
    PurchaseQuoteUpdateStatus,
)
from app.schemas.quote_import_schema import (
    PurchaseQuoteImportCommitRequest,
    PurchaseQuoteImportPreviewResponse,
)
from app.services.purchase_quote_service import PurchaseQuoteService
from app.services.purchase_quote_pdf_service import build_purchase_quote_pdf
from app.services.quote_import_service import QuoteImportService

router = APIRouter(prefix="/purchase-quotes", tags=["purchase-quotes"])

@router.get("", response_model=PurchaseQuoteListResponse)
@limiter.limit("30/minute")
def get_purchase_quotes(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str | None = Query(default=None),
    supplier_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = PurchaseQuoteService(db)
    return service.get_purchase_quotes(
        page=page,
        page_size=page_size,
        status_value=status,
        supplier_id=supplier_id,
    )

@router.get("/{purchase_quote_id}", response_model=PurchaseQuoteResponse)
def get_purchase_quote(
    purchase_quote_id: int,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = PurchaseQuoteService(db)
    return service.get_by_id(purchase_quote_id)

@router.get("/{purchase_quote_id}/download-pdf")
@limiter.limit("10/minute")
def download_purchase_quote_pdf(
    request: Request,
    purchase_quote_id: int,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = PurchaseQuoteService(db)
    quote = service.get_by_id(purchase_quote_id)
    pdf_bytes = build_purchase_quote_pdf(quote)
    filename = f"presupuesto-compra-{quote.quote_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@router.post(
    "",
    response_model=PurchaseQuoteResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute")
def create_purchase_quote(
    request: Request,
    data: PurchaseQuoteCreate,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = PurchaseQuoteService(db)
    return service.create(data, current_user)

@router.put("/{purchase_quote_id}", response_model=PurchaseQuoteResponse)
@limiter.limit("5/minute")
def update_purchase_quote(
    request: Request,
    purchase_quote_id: int,
    data: PurchaseQuoteUpdate,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    service = PurchaseQuoteService(db)
    return service.update(purchase_quote_id, data)

@router.patch(
    "/{purchase_quote_id}/items/{item_id}/link-product",
    response_model=PurchaseQuoteItemResponse,
)
@limiter.limit("5/minute")
def link_purchase_quote_item_to_product(
    request: Request,
    purchase_quote_id: int,
    item_id: int,
    data: PurchaseQuoteLinkProduct,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    service = PurchaseQuoteService(db)
    return service.link_item_to_product(purchase_quote_id, item_id, data)

@router.patch("/{purchase_quote_id}/status", response_model=PurchaseQuoteResponse)
@limiter.limit("5/minute")
def update_purchase_quote_status(
    request: Request,
    purchase_quote_id: int,
    data: PurchaseQuoteUpdateStatus,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = PurchaseQuoteService(db)
    return service.update_status(purchase_quote_id, data.status, current_user=current_user)

@router.post(
    "/import/preview-file",
    response_model=PurchaseQuoteImportPreviewResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("5/minute")
async def preview_purchase_quote_file(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = QuoteImportService(db)
    file_bytes = await file.read()
    return service.preview_purchase_quote(file_bytes)

@router.post(
    "/import/commit",
    response_model=PurchaseQuoteResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute")
def commit_purchase_quote_import(
    request: Request,
    data: PurchaseQuoteImportCommitRequest,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = QuoteImportService(db)
    return service.commit_purchase_quote(data, current_user)