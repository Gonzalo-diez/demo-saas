from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session
from app.core.rate_limit import limiter
from app.db.base import get_db, get_db_with_commit
from app.core.dependencies import get_current_active_user
from app.models.sales_rep_model import SalesRep
from app.schemas.account_movement_schema import (
    ClientAccountMovementListResponse,
    ClientAccountMovementResponse,
    ClientPaymentCreate,
)
from app.schemas.account_movement_stats_schema import (
    AccountAgingSummary,
    AccountBalanceHistoryPoint,
    AccountBalanceSummary,
    AccountRankingItem,
)
from app.services.client_account_movement_service import ClientAccountMovementService

router = APIRouter(
    prefix="/client-account-movements",
    tags=["client-account-movements"],
)

@router.get("/stats/summary", response_model=AccountBalanceSummary)
def get_client_balance_summary(
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = ClientAccountMovementService(db)
    return service.get_balance_summary()

@router.get("/stats/aging", response_model=AccountAgingSummary)
def get_client_aging_summary(
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = ClientAccountMovementService(db)
    return service.get_aging_summary()

@router.get("/stats/ranking", response_model=list[AccountRankingItem])
def get_client_ranking(
    limit: int = Query(10, ge=1, le=50),
    order: str = Query("debtors", pattern="^(debtors|favor)$"),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = ClientAccountMovementService(db)
    return service.get_ranking(limit=limit, order=order)

@router.get(
    "/by-client/{client_id}/balance-history",
    response_model=list[AccountBalanceHistoryPoint],
)
def get_client_balance_history(
    client_id: int,
    limit: int = Query(60, ge=1, le=200),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = ClientAccountMovementService(db)
    return service.get_balance_history(client_id, limit=limit)

@router.get("", response_model=ClientAccountMovementListResponse)
@limiter.limit("30/minute")
def get_client_account_movements(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    client_id: int | None = Query(default=None, gt=0),
    movement_type: str | None = Query(default=None),
    reference_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = ClientAccountMovementService(db)
    return service.get_movements(
        page=page,
        page_size=page_size,
        client_id=client_id,
        movement_type=movement_type,
        reference_type=reference_type,
    )

@router.get("/{movement_id}", response_model=ClientAccountMovementResponse)
def get_client_account_movement(
    movement_id: int,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = ClientAccountMovementService(db)
    return service.get_by_id(movement_id)

@router.get(
    "/by-client/{client_id}",
    response_model=ClientAccountMovementListResponse,
)
@limiter.limit("30/minute")
def get_movements_by_client(
    request: Request,
    client_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = ClientAccountMovementService(db)
    return service.get_client_movements(
        client_id=client_id,
        page=page,
        page_size=page_size,
    )

@router.post(
    "/by-client/{client_id}/payments",
    response_model=ClientAccountMovementResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("15/minute")
def register_client_payment(
    request: Request,
    client_id: int,
    data: ClientPaymentCreate,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = ClientAccountMovementService(db)
    return service.register_payment(client_id, data, current_user)
