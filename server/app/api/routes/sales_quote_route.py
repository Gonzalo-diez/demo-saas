from fastapi import APIRouter, Depends, Query, Request, UploadFile, File, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.core.rate_limit import limiter
from app.db.base import get_db, get_db_with_commit
from app.core.dependencies import get_current_active_user
from app.models.sales_rep_model import SalesRep
from app.schemas.sales_quote_schema import (
    SalesQuoteCreate,
    SalesQuoteItemResponse,
    SalesQuoteLinkProduct,
    SalesQuoteListResponse,
    SalesQuoteResponse,
    SalesQuoteUpdate,
    SalesQuoteUpdateStatus,
)
from app.schemas.account_movement_schema import (
    SalesQuotePaymentCreate,
    SalesQuotePaymentListResponse,
)
from app.schemas.quote_import_schema import (
    SalesQuoteImportCommitRequest,
    SalesQuoteImportPreviewResponse,
)
from app.services.sales_quote_service import SalesQuoteService
from app.services.sales_quote_pdf_service import build_sales_quote_pdf
from app.services.quote_import_service import QuoteImportService

router = APIRouter(prefix="/sales-quotes", tags=["sales-quotes"])

@router.get("", response_model=SalesQuoteListResponse)
@limiter.limit("30/minute")
def get_sales_quotes(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str | None = Query(default=None),
    client_id: int | None = Query(default=None),
    from_orders: bool | None = Query(
        default=None,
        description="true = solo presupuestos generados por un pedido; false = solo cotizaciones sueltas",
    ),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = SalesQuoteService(db)
    return service.get_sales_quotes(
        page=page,
        page_size=page_size,
        status_value=status,
        client_id=client_id,
        from_orders=from_orders,
    )

@router.get("/{sales_quote_id}", response_model=SalesQuoteResponse)
def get_sales_quote(
    sales_quote_id: int,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = SalesQuoteService(db)
    return service.get_by_id(sales_quote_id)

@router.get("/{sales_quote_id}/download-pdf")
@limiter.limit("10/minute")
def download_sales_quote_pdf(
    request: Request,
    sales_quote_id: int,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = SalesQuoteService(db)
    quote = service.get_by_id(sales_quote_id)
    pdf_bytes = build_sales_quote_pdf(quote)
    filename = f"presupuesto-venta-{quote.quote_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@router.post(
    "",
    response_model=SalesQuoteResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute")
def create_sales_quote(
    request: Request,
    data: SalesQuoteCreate,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = SalesQuoteService(db)
    return service.create(data, current_user)

@router.put("/{sales_quote_id}", response_model=SalesQuoteResponse)
@limiter.limit("5/minute")
def update_sales_quote(
    request: Request,
    sales_quote_id: int,
    data: SalesQuoteUpdate,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    service = SalesQuoteService(db)
    return service.update(sales_quote_id, data)

@router.patch(
    "/{sales_quote_id}/items/{item_id}/link-product",
    response_model=SalesQuoteItemResponse,
)
@limiter.limit("5/minute")
def link_sales_quote_item_to_product(
    request: Request,
    sales_quote_id: int,
    item_id: int,
    data: SalesQuoteLinkProduct,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    service = SalesQuoteService(db)
    return service.link_item_to_product(sales_quote_id, item_id, data)

@router.patch("/{sales_quote_id}/status", response_model=SalesQuoteResponse)
@limiter.limit("5/minute")
def update_sales_quote_status(
    request: Request,
    sales_quote_id: int,
    data: SalesQuoteUpdateStatus,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = SalesQuoteService(db)
    return service.update_status(sales_quote_id, data.status, current_user=current_user)

@router.post(
    "/{sales_quote_id}/payments",
    response_model=SalesQuotePaymentListResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("15/minute")
def register_sales_quote_payment(
    request: Request,
    sales_quote_id: int,
    data: SalesQuotePaymentCreate,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    """
    Registra un cobro sobre un presupuesto generado por un pedido. Descuenta la
    deuda de la cuenta corriente del cliente (mismo efecto que un cobro
    imputado desde /client-account-movements).
    """
    service = SalesQuoteService(db)
    return service.register_online_payment(sales_quote_id, data, current_user)

@router.get(
    "/{sales_quote_id}/payments",
    response_model=SalesQuotePaymentListResponse,
)
def get_sales_quote_payments(
    sales_quote_id: int,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = SalesQuoteService(db)
    return service.get_online_payments(sales_quote_id)

@router.post(
    "/import/preview-file",
    response_model=SalesQuoteImportPreviewResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("5/minute")
async def preview_sales_quote_file(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = QuoteImportService(db)
    file_bytes = await file.read()
    return service.preview_sales_quote(file_bytes)

@router.post(
    "/import/commit",
    response_model=SalesQuoteResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute")
def commit_sales_quote_import(
    request: Request,
    data: SalesQuoteImportCommitRequest,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = QuoteImportService(db)
    return service.commit_sales_quote(data, current_user)