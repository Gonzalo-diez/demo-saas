from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.product_model import Product
from app.models.product_purchase_model import ProductPurchase
from app.models.sales_rep_model import SalesRep
from app.repositories.product_purchase_repository import ProductPurchaseRepository
from app.schemas.product_purchase_schema import (
    ProductPurchaseCreate,
    ProductPurchaseListResponse,
    ProductPurchaseResponse,
    ProductPurchaseSummary,
)
from app.services.inventory_movement_service import InventoryMovementService
from app.utils.pricing import price_from_markup

_CENTS = Decimal("0.01")


class ProductPurchaseService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProductPurchaseRepository(db)

    # ------------------------------------------------------------------
    # Registro (lo usan el alta de producto, remitos e importaciones)
    # ------------------------------------------------------------------
    def record(
        self,
        *,
        product_id: int,
        quantity: int,
        unit_cost,
        source: str,
        purchase_date: date | None = None,
        markup_percent=None,
        sale_price=None,
        expiry_date: date | None = None,
        reference_id: int | None = None,
        notes: str | None = None,
        created_by: int | None = None,
    ) -> ProductPurchase:
        """Deja asentada una compra en el historial. No toca stock ni costos: eso lo hace el caller."""
        purchase = ProductPurchase(
            product_id=product_id,
            purchase_date=purchase_date or date.today(),
            quantity=int(quantity),
            unit_cost=Decimal(str(unit_cost or 0)).quantize(_CENTS),
            markup_percent=markup_percent,
            sale_price=sale_price,
            expiry_date=expiry_date,
            source=source,
            reference_id=reference_id,
            notes=notes,
            created_by=created_by,
        )
        return self.repo.add(purchase)

    # ------------------------------------------------------------------
    # Compra manual de un producto existente
    # ------------------------------------------------------------------
    def create_purchase(
        self,
        product_id: int,
        data: ProductPurchaseCreate,
        current_user: SalesRep | None = None,
    ) -> ProductPurchase:
        # Lock del producto: stock y costo promedio se calculan sobre el estado actual.
        product = (
            self.db.query(Product)
            .filter(Product.id == product_id)
            .with_for_update()
            .first()
        )
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado"
            )

        today = date.today()
        purchase_date = data.purchase_date or today
        if purchase_date > today + timedelta(days=1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha de la compra no puede ser futura",
            )
        if data.expiry_date is not None and data.expiry_date < purchase_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El vencimiento no puede ser anterior a la fecha de compra",
            )

        # Precio de venta de esta compra
        sale_price = None
        markup = data.markup_percent
        if markup is not None:
            sale_price = price_from_markup(data.unit_cost, markup)
        elif data.sale_price is not None:
            sale_price = data.sale_price.quantize(_CENTS)

        # Costo promedio ponderado (antes de sumar el stock) y movimiento de inventario.
        from app.services.product_service import ProductService  # evita import circular

        ProductService(self.db).apply_weighted_average_cost(
            product, data.quantity, data.unit_cost
        )
        InventoryMovementService(self.db).apply_movement(
            product_id=product.id,
            movement_type="purchase",
            quantity=Decimal(data.quantity),
            reference_type="manual_adjustment",
            notes=data.notes or "Compra registrada desde el historial del producto",
        )

        if sale_price is not None and data.update_product_price:
            product.unit_price = sale_price
            product.markup_percent = markup  # None si se fijó el precio a mano

        return self.record(
            product_id=product.id,
            quantity=data.quantity,
            unit_cost=data.unit_cost,
            source="manual",
            purchase_date=purchase_date,
            markup_percent=markup,
            sale_price=sale_price,
            expiry_date=data.expiry_date,
            notes=data.notes,
            created_by=current_user.id if current_user else None,
        )

    # ------------------------------------------------------------------
    # Historial
    # ------------------------------------------------------------------
    def list_purchases(
        self, product_id: int, *, page: int = 1, page_size: int = 20
    ) -> ProductPurchaseListResponse:
        if page < 1 or page_size < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="page y page_size deben ser mayores o iguales a 1",
            )
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado"
            )

        items, total = self.repo.list_for_product(
            product_id, page=page, page_size=page_size
        )
        stats = self.repo.summary_for_product(product_id, date.today())

        average = None
        if stats["total_quantity"] > 0:
            average = (Decimal(stats["total_cost"]) / stats["total_quantity"]).quantize(_CENTS)

        responses = []
        for item in items:
            response = ProductPurchaseResponse.model_validate(item)
            response.created_by_name = item.creator.name if item.creator else None
            responses.append(response)

        return ProductPurchaseListResponse(
            items=responses,
            total=total,
            page=page,
            page_size=page_size,
            summary=ProductPurchaseSummary(
                purchases_count=stats["count"],
                total_quantity=stats["total_quantity"],
                average_cost=average,
                last_cost=stats["last_cost"],
                min_cost=stats["min_cost"],
                max_cost=stats["max_cost"],
                next_expiry_date=stats["next_expiry_date"],
            ),
        )
