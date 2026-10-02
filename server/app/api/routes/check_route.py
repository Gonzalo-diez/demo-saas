from datetime import date
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.rate_limit import limiter
from app.db.base import get_db, get_db_with_commit
from app.core.dependencies import get_current_active_user
from app.models.sales_rep_model import SalesRep
from app.schemas.check_schema import (
    CheckListResponse,
    CheckPendingSummaryResponse,
    CheckRejectRequest,
    CheckResponse,
    DocumentPendingChecksResponse,
    IssuedCheckCreate,
    ReceivedCheckCreate,
)
from app.services.check_service import CheckService

router = APIRouter(prefix="/checks", tags=["checks"])


@router.get("", response_model=CheckListResponse)
def get_checks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    direction: str | None = Query(default=None, pattern="^(received|issued)$"),
    status_value: str | None = Query(default=None, alias="status"),
    client_id: int | None = Query(default=None, gt=0),
    supplier_id: int | None = Query(default=None, gt=0),
    due_before: date | None = Query(
        default=None,
        description="Cheques que vencen en esta fecha o antes (para ver próximos a vencer)",
    ),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = CheckService(db)
    return service.get_checks(
        page=page,
        page_size=page_size,
        direction=direction,
        status_value=status_value,
        client_id=client_id,
        supplier_id=supplier_id,
        due_before=due_before,
    )


@router.get("/{check_id}", response_model=CheckResponse)
def get_check(
    check_id: int,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = CheckService(db)
    return service.get_by_id(check_id)


@router.get(
    "/by-client/{client_id}/pending-summary",
    response_model=CheckPendingSummaryResponse,
)
def get_pending_checks_for_client(
    client_id: int,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    """Total de cheques recibidos de este cliente en cartera (pendientes
    o depositados, todavía no acreditados/rechazados)."""
    service = CheckService(db)
    return service.get_pending_summary_for_client(client_id)


@router.get(
    "/by-supplier/{supplier_id}/pending-summary",
    response_model=CheckPendingSummaryResponse,
)
def get_pending_checks_for_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    """Total de cheques emitidos a este proveedor todavía en cartera."""
    service = CheckService(db)
    return service.get_pending_summary_for_supplier(supplier_id)


@router.get(
    "/by-document/{document_type}/{invoice_id}/pending",
    response_model=DocumentPendingChecksResponse,
)
def get_pending_checks_for_document(
    document_type: str,
    invoice_id: int,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    """
    Cheques en cartera imputados a este remito/presupuesto puntual
    (document_type: sales_invoice | sales_quote | purchase_invoice |
    purchase_quote). Para mostrar en la ficha del documento algo como
    "tiene un cheque pendiente de $X".
    """
    service = CheckService(db)
    return service.get_pending_checks_for_document(document_type, invoice_id)


@router.post(
    "/by-client/{client_id}",
    response_model=CheckResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("15/minute")
def register_received_check(
    request: Request,
    client_id: int,
    data: ReceivedCheckCreate,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    """
    Registra un cheque recibido de un cliente como cobro. Queda
    'pendiente': no afecta el saldo del cliente hasta que se acredite
    (POST /checks/{check_id}/credit).
    """
    service = CheckService(db)
    return service.register_received(client_id, data, current_user)


@router.post(
    "/by-supplier/{supplier_id}",
    response_model=CheckResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("15/minute")
def register_issued_check(
    request: Request,
    supplier_id: int,
    data: IssuedCheckCreate,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    """
    Registra un cheque propio emitido a un proveedor como pago. Queda
    'pendiente': no afecta la deuda con el proveedor hasta que se
    acredite (POST /checks/{check_id}/credit).
    """
    service = CheckService(db)
    return service.register_issued(supplier_id, data, current_user)


@router.post("/{check_id}/deposit", response_model=CheckResponse)
def deposit_check(
    check_id: int,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    service = CheckService(db)
    return service.mark_as_deposited(check_id)


@router.post("/{check_id}/credit", response_model=CheckResponse)
def credit_check(
    check_id: int,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    """
    Acredita el cheque: recién en este momento se genera el
    movimiento de cuenta corriente (cobro o pago) y se aplican las
    imputaciones pendientes.
    """
    service = CheckService(db)
    return service.credit(check_id, current_user)


@router.post("/{check_id}/reject", response_model=CheckResponse)
def reject_check(
    check_id: int,
    data: CheckRejectRequest,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    """
    Rechaza el cheque (rebotó). Como nunca se tocó el saldo, no hay
    nada que revertir.
    """
    service = CheckService(db)
    return service.reject(check_id, data)