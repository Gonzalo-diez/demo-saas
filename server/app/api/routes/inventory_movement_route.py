from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from app.core.rate_limit import limiter
from app.db.base import get_db
from app.core.dependencies import get_current_active_user
from app.models.sales_rep_model import SalesRep
from app.schemas.inventory_movement_schema import (
    InventoryMovementListResponse,
    InventoryMovementResponse,
)
from app.services.inventory_movement_service import InventoryMovementService

router = APIRouter(
    prefix="/inventory-movements",
    tags=["inventory-movements"],
)

@router.get("", response_model=InventoryMovementListResponse)
@limiter.limit("30/minute")
def get_inventory_movements(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    product_id: int | None = Query(default=None, gt=0),
    movement_type: str | None = Query(default=None),
    reference_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = InventoryMovementService(db)
    return service.get_inventory_movements(
        page=page,
        page_size=page_size,
        product_id=product_id,
        movement_type=movement_type,
        reference_type=reference_type,
    )

@router.get("/{movement_id}", response_model=InventoryMovementResponse)
def get_inventory_movement(
    movement_id: int,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = InventoryMovementService(db)
    return service.get_by_id(movement_id)