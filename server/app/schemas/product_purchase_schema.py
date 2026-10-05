from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PurchaseSource = Literal["initial_stock", "manual", "purchase_invoice", "import"]


class ProductPurchaseCreate(BaseModel):
    """Compra de mercadería de un producto ya cargado (suma stock y queda en el historial)."""

    quantity: int = Field(..., gt=0, le=10_000_000)
    unit_cost: Decimal = Field(..., ge=0, max_digits=12, decimal_places=2)

    # Precio de venta de esta compra: con un % de remarque sobre el costo (se redondea al
    # peso entero) o fijado a mano. Si no se manda ninguno, el precio no se toca.
    markup_percent: Decimal | None = Field(default=None, ge=0, le=10_000)
    sale_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)

    expiry_date: date | None = None
    purchase_date: date | None = None  # por defecto, hoy
    notes: str | None = Field(default=None, max_length=500)

    # Si es True (y hay remarque o precio), el producto pasa a venderse a ese precio.
    update_product_price: bool = True

    @model_validator(mode="after")
    def _one_way_to_set_price(self):
        if self.markup_percent is not None and self.sale_price is not None:
            raise ValueError("Elegí un % de remarque o un precio de venta, no los dos")
        return self


class ProductPurchaseResponse(BaseModel):
    id: int
    product_id: int
    purchase_date: date
    quantity: int
    unit_cost: Decimal
    markup_percent: Decimal | None = None
    sale_price: Decimal | None = None
    expiry_date: date | None = None
    source: str
    reference_id: int | None = None
    notes: str | None = None
    created_by: int | None = None
    created_by_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductPurchaseSummary(BaseModel):
    purchases_count: int
    total_quantity: int
    # Costo promedio ponderado de TODAS las compras registradas.
    average_cost: Decimal | None = None
    last_cost: Decimal | None = None
    min_cost: Decimal | None = None
    max_cost: Decimal | None = None
    # Vencimiento más cercano (de hoy en adelante) entre las compras cargadas. Es una
    # referencia: no se descuenta lo ya vendido de cada compra.
    next_expiry_date: date | None = None


class ProductPurchaseListResponse(BaseModel):
    items: list[ProductPurchaseResponse]
    total: int
    page: int
    page_size: int
    summary: ProductPurchaseSummary
