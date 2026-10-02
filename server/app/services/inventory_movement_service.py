import math
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.constants.inventory_movement_constant import (
    ALLOWED_INVENTORY_MOVEMENT_TYPES,
    ALLOWED_INVENTORY_REFERENCE_TYPES,
)
from app.models.inventory_movement_model import InventoryMovement
from app.models.product_model import Product
from app.repositories.inventory_movement_repository import InventoryMovementRepository
from app.repositories.product_repository import ProductRepository
from app.core.config import get_settings
from app.services.notification_alert_service import (
    NotificationAlertService,
    get_stock_alert_type,
)

class InventoryMovementService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = InventoryMovementRepository(db)
        self.product_repo = ProductRepository(db)
        
    def apply_movement(
        self,
        *,
        product_id: int,
        movement_type: str,
        quantity: Decimal,
        reference_type: str | None = None,
        reference_id: int | None = None,
        notes: str | None = None,
    ):
        if movement_type not in ALLOWED_INVENTORY_MOVEMENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de movimiento inválido",
            )

        if (
            reference_type is not None
            and reference_type not in ALLOWED_INVENTORY_REFERENCE_TYPES
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de referencia inválido",
            )

        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La cantidad debe ser mayor a 0",
            )

        product = (
            self.db.query(Product)
            .filter(Product.id == product_id)
            .with_for_update()
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado",
            )

        incoming_types = {
            "purchase",
            "adjustment_in",
            "initial_stock",
            "sale_reversal",
            "inventory_found",
        }

        outgoing_types = {
            "sale",
            "adjustment_out",
            "purchase_reversal",
            "inventory_loss",
        }

        if movement_type in incoming_types:
            is_outgoing = False
        elif movement_type in outgoing_types:
            is_outgoing = True
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de movimiento inválido",
            )

        stock_before = Decimal(product.stock_current)

        if is_outgoing:

            if stock_before < quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Stock insuficiente para "
                        f"'{product.name}'. "
                        f"Disponible: {stock_before}"
                    ),
                )

            stock_after = stock_before - quantity

        else:
            stock_after = stock_before + quantity
            
        unit_cost = Decimal(product.unit_cost)
        unit_price = Decimal(product.unit_price)

        movement = InventoryMovement(
            product_id=product.id,
            movement_type=movement_type,
            quantity=quantity,
            stock_before=stock_before,
            stock_after=stock_after,
            unit_cost=unit_cost,
            unit_price=unit_price,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
        )

        product.stock_current = stock_after

        self.db.add(movement)

        self._sync_stock_alert(product, stock_before, stock_after)

        return movement

    def _sync_stock_alert(
        self,
        product: Product,
        stock_before: Decimal,
        stock_after: Decimal,
    ) -> None:
        """
        Avisos de stock bajo / cerca del mínimo / sin stock. Si el producto
        estaba y sigue estando sano no hace nada (evita consultas de más en
        ventas e imports grandes); el barrido diario reconcilia el resto.
        """
        margin = get_settings().STOCK_NEAR_MIN_MARGIN_PERCENT
        before = get_stock_alert_type(
            stock_before, product.stock_min,
            margin_percent=margin, is_active=bool(product.is_active),
        )
        after = get_stock_alert_type(
            stock_after, product.stock_min,
            margin_percent=margin, is_active=bool(product.is_active),
        )
        if before is None and after is None:
            return

        NotificationAlertService(self.db).safe_sync_product_stock(product)

    def get_by_id(self, movement_id: int):
        movement = self.repo.get_by_id(movement_id)
        if not movement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movimiento de inventario no encontrado",
            )
        return movement

    def get_inventory_movements(
        self,
        page: int = 1,
        page_size: int = 20,
        product_id: int | None = None,
        movement_type: str | None = None,
        reference_type: str | None = None,
    ):
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="page debe ser mayor o igual a 1",
            )

        if page_size < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="page_size debe ser mayor o igual a 1",
            )

        if product_id is not None:
            product = self.product_repo.get_product_by_id(product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Producto no encontrado",
                )

        if (
            movement_type is not None
            and movement_type not in ALLOWED_INVENTORY_MOVEMENT_TYPES
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de movimiento inválido",
            )

        if (
            reference_type is not None
            and reference_type not in ALLOWED_INVENTORY_REFERENCE_TYPES
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de referencia inválido",
            )

        items, total = self.repo.get_inventory_movements(
            page=page,
            page_size=page_size,
            product_id=product_id,
            movement_type=movement_type,
            reference_type=reference_type,
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
        
    def get_product_inventory_movements(
        self,
        product_id: int,
        page: int = 1,
        page_size: int = 20,
    ):
        return self.get_inventory_movements(
            page=page,
            page_size=page_size,
            product_id=product_id,
        )