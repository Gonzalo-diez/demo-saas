from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session
from app.core.rate_limit import limiter
from app.db.base import get_db, get_db_with_commit
from app.core.dependencies import get_current_active_user
from app.models.sales_rep_model import SalesRep
from app.schemas.account_movement_schema import (
    SupplierAccountMovementListResponse,
    SupplierAccountMovementResponse,
    SupplierPaymentCreate,
)
from app.schemas.account_movement_stats_schema import (
    AccountAgingSummary,
    AccountBalanceHistoryPoint,
    AccountBalanceSummary,
    AccountRankingItem,
)
from app.services.supplier_account_movement_service import SupplierAccountMovementService

router = APIRouter(
    prefix="/supplier-account-movements",
    tags=["supplier-account-movements"],
)

@router.get("/stats/summary", response_model=AccountBalanceSummary)
def get_supplier_balance_summary(
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = SupplierAccountMovementService(db)
    return service.get_balance_summary()

@router.get("/stats/aging", response_model=AccountAgingSummary)
def get_supplier_aging_summary(
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = SupplierAccountMovementService(db)
    return service.get_aging_summary()

@router.get("/stats/ranking", response_model=list[AccountRankingItem])
def get_supplier_ranking(
    limit: int = Query(10, ge=1, le=50),
    order: str = Query("debtors", pattern="^(debtors|favor)$"),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = SupplierAccountMovementService(db)
    return service.get_ranking(limit=limit, order=order)

@router.get(
    "/by-supplier/{supplier_id}/balance-history",
    response_model=list[AccountBalanceHistoryPoint],
)
def get_supplier_balance_history(
    supplier_id: int,
    limit: int = Query(60, ge=1, le=200),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = SupplierAccountMovementService(db)
    return service.get_balance_history(supplier_id, limit=limit)

@router.get("", response_model=SupplierAccountMovementListResponse)
@limiter.limit("30/minute")
def get_supplier_account_movements(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supplier_id: int | None = Query(default=None, gt=0),
    movement_type: str | None = Query(default=None),
    reference_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = SupplierAccountMovementService(db)
    return service.get_movements(
        page=page,
        page_size=page_size,
        supplier_id=supplier_id,
        movement_type=movement_type,
        reference_type=reference_type,
    )

@router.get("/{movement_id}", response_model=SupplierAccountMovementResponse)
def get_supplier_account_movement(
    movement_id: int,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = SupplierAccountMovementService(db)
    return service.get_by_id(movement_id)

@router.get(
    "/by-supplier/{supplier_id}",
    response_model=SupplierAccountMovementListResponse,
)
@limiter.limit("30/minute")
def get_movements_by_supplier(
    request: Request,
    supplier_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = SupplierAccountMovementService(db)
    return service.get_supplier_movements(
        supplier_id=supplier_id,
        page=page,
        page_size=page_size,
    )

@router.post(
    "/by-supplier/{supplier_id}/payments",
    response_model=SupplierAccountMovementResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("15/minute")
def register_supplier_payment(
    request: Request,
    supplier_id: int,
    data: SupplierPaymentCreate,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = SupplierAccountMovementService(db)
    return service.register_payment(supplier_id, data, current_user)
