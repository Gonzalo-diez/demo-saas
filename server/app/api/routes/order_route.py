import functools
import logging

from pydantic import ValidationError
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from app.db.base import get_db, get_db_with_commit
from app.core.rate_limit import limiter
from app.core.dependencies import get_current_active_user, get_current_active_client
from app.core.order_edit_token import get_order_edit_token_tenant_id
from app.db.tenant_context import set_tenant
from app.models.tenant_model import Tenant
from app.models.sales_rep_model import SalesRep
from app.models.client_model import Client
from app.services.order_service import OrderService
from app.services import whatsapp_service
from app.schemas.order_schema import (
    OrderCreateB2B,
    OrderCreateShop,
    OrderEditB2B,
    OrderEditShop,
    OrderUpdateB2B,
    OrderUpdateShop,
    OrderUpdateStatus,
    OrderResponse,
    OrderPublicResponse,
    OrderListResponse,
    OrderStatus,
    OrderScheduleDelivery,
)

router = APIRouter(prefix="/orders", tags=["Orders"])
logger = logging.getLogger("order_route")


def _value_errors_as_http(func):
    """
    Los services de pedidos reportan errores de negocio con ValueError
    ("Orden no encontrada", "Transición inválida", ...). Sin esta traducción
    llegaban al cliente como 500. Va debajo de @limiter.limit / @router.*.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError:
            raise
        except ValueError as exc:
            detail = str(exc)
            code = (
                status.HTTP_404_NOT_FOUND
                if "no encontrad" in detail.lower()
                else status.HTTP_400_BAD_REQUEST
            )
            raise HTTPException(status_code=code, detail=detail)

    return wrapper

@router.get("", response_model=OrderListResponse)
@limiter.limit("30/minute")
def list_orders(
    request: Request,
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    sales_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = OrderService(db)
    return service.list_orders(
        status=status_filter,
        sales_type=sales_type,
        page=page,
        page_size=page_size,
    )

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = OrderService(db)
    order = service.get_order(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden no encontrada.",
        )

    return order

@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def create_order_shop(
    request: Request,
    order_in: OrderCreateShop,
    db: Session = Depends(get_db_with_commit),
    current_client: Client = Depends(get_current_active_client),
):
    service = OrderService(db)
    try:
        return service.create_order_shop(obj_in=order_in, current_client=current_client)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

@router.post("/b2b", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
@_value_errors_as_http
def create_order_b2b(
    request: Request,
    order_in: OrderCreateB2B,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = OrderService(db)

    return service.create_order_b2b(
        obj_in=order_in,
        current_user=current_user,
    )
    
@router.put("/{order_id}", response_model=OrderResponse)
@limiter.limit("10/minute")
@_value_errors_as_http
def update_order_shop(
    request: Request,
    order_id: int,
    order_in: OrderUpdateShop,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    service = OrderService(db)

    return service.update_order_shop(
        order_id=order_id,
        obj_in=order_in,
    )

@router.put("/b2b/{order_id}", response_model=OrderResponse)
@limiter.limit("5/minute")
@_value_errors_as_http
def update_order_b2b(
    request: Request,
    order_id: int,
    order_in: OrderUpdateB2B,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    service = OrderService(db)

    return service.update_order_b2b(
        order_id=order_id,
        obj_in=order_in,
    )

@router.patch("/{order_id}/status", response_model=OrderResponse)
@_value_errors_as_http
def update_order_status(
    order_id: int,
    status_data: OrderUpdateStatus,
    db: Session = Depends(get_db_with_commit),
    current_user: SalesRep = Depends(get_current_active_user),
):
    service = OrderService(db)

    return service.update_order_status(
        order_id=order_id,
        status=status_data.status,
        current_user=current_user,
    )
    
@router.patch("/shop/{order_id}/edit", response_model=OrderResponse)
@limiter.limit("5/minute")
@_value_errors_as_http
def edit_order_shop(
    request: Request,
    order_id: int,
    order_in: OrderEditShop,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    service = OrderService(db)

    return service.edit_order_shop(
        order_id=order_id,
        obj_in=order_in,
    )
    
@router.patch("/b2b/{order_id}/edit", response_model=OrderResponse)
@limiter.limit("5/minute")
@_value_errors_as_http
def edit_order_b2b(
    request: Request,
    order_id: int,
    order_in: OrderEditB2B,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    service = OrderService(db)

    return service.edit_order_b2b(
        order_id=order_id,
        obj_in=order_in,
    )
    
@router.patch("/{order_id}/schedule-delivery", response_model=OrderResponse)
@limiter.limit("10/minute")
@_value_errors_as_http
def schedule_delivery(
    request: Request,
    order_id: int,
    payload: OrderScheduleDelivery,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    service = OrderService(db)

    return service.schedule_delivery(
        order_id=order_id,
        scheduled_delivery_date=payload.scheduled_delivery_date,
    )

# ==========================================================
# Acceso público con token: el cliente edita SU pedido sin
# necesitar login de sales rep (ej: link mandado por WhatsApp).
# ==========================================================

def _require_valid_order_edit_token(order_id: int, token: str, db: Session) -> None:
    """
    Valida el link y ata la sesión al tenant del pedido (el tenant viaja firmado
    dentro del token: en estos endpoints públicos no hay otra forma de saberlo).
    """
    invalid = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Link inválido o vencido. Pedí uno nuevo por WhatsApp.",
    )

    tenant_id = get_order_edit_token_tenant_id(token, order_id)
    if tenant_id is None:
        raise invalid

    tenant = db.get(Tenant, tenant_id)
    if tenant is None or not tenant.is_active:
        raise invalid

    set_tenant(db, tenant_id)


@router.get("/public/{order_id}/{token}", response_model=OrderPublicResponse)
@limiter.limit("20/minute")
def get_order_public(
    request: Request,
    order_id: int,
    token: str,
    db: Session = Depends(get_db),
):
    _require_valid_order_edit_token(order_id, token, db)

    service = OrderService(db)

    order = service.get_order(order_id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden no encontrada.",
        )

    return order

@router.patch(
    "/public/{order_id}/{token}/edit",
    response_model=OrderPublicResponse,
)
@limiter.limit("10/minute")
@_value_errors_as_http
def edit_order_public(
    request: Request,
    order_id: int,
    token: str,
    order_in: OrderEditShop,
    db: Session = Depends(get_db_with_commit),
):
    _require_valid_order_edit_token(order_id, token, db)

    service = OrderService(db)

    updated_order = service.edit_order_shop(
        order_id=order_id,
        obj_in=order_in,
    )

    try:
        items_summary = "\n".join(
            f"• {item.quantity}x {item.product_name_snapshot}"
            for item in updated_order.items
        )
        whatsapp_service.send_order_status_whatsapp(
            updated_order,
            f"Listo, actualizamos tu pedido #{updated_order.id}:\n\n"
            f"{items_summary}\n\n"
            f"Nuevo total: {updated_order.currency} {updated_order.total_amount}",
        )
    except Exception:
        # Si falla el aviso por WhatsApp no queremos que la edición
        # (que ya se guardó bien en la base) aparente haber fallado.
        logger.exception("[order_route] no se pudo avisar por WhatsApp la edición del pedido #%s", order_id)

    return updated_order