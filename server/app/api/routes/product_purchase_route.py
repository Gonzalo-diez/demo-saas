from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.db.base import get_db, get_db_with_commit
from app.models.sales_rep_model import SalesRep
from app.schemas.product_purchase_schema import (
    ProductPurchaseCreate,
    ProductPurchaseListResponse,
    ProductPurchaseResponse,
)
from app.services.product_purchase_service import ProductPurchaseService

router = APIRouter(prefix="/products/{product_id}/purchases", tags=["Product Purchases"])


@router.get("/", response_model=ProductPurchaseListResponse)
def list_product_purchases(
    product_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    """Historial de compras del producto (la más reciente primero) con un resumen de costos."""
    return ProductPurchaseService(db).list_purchases(
        product_id, page=page, page_size=page_size
    )


@router.post("/", response_model=ProductPurchaseResponse, status_code=status.HTTP_201_CREATED)
def create_product_purchase(
    product_id: int,
    data: ProductPurchaseCreate,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    """
    Registra una compra: suma stock, recalcula el costo promedio y la deja en el historial.
    Con `markup_percent` calcula el precio de venta (costo + remarque, redondeado al peso).
    """
    purchase = ProductPurchaseService(db).create_purchase(product_id, data, current_user)
    response = ProductPurchaseResponse.model_validate(purchase)
    response.created_by_name = current_user.name
    return response
