from decimal import Decimal
from datetime import date, datetime
from typing import Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.utils.pricing import price_from_markup

ProductSort = Literal[
    "name-asc",
    "name-desc",
    "price-asc",
    "price-desc",
]

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

    description: str | None = Field(default=None, max_length=2000)

    slug: str | None = Field(default=None, min_length=1, max_length=255)

    unit_cost: Decimal = Field(..., ge=0)
    unit_price: Decimal = Field(..., ge=0)

    currency: str = Field(default="ARS", min_length=1, max_length=10)

    stock_current: int = Field(default=0, ge=0)
    stock_min: int = Field(default=0, ge=0)

    sku: str | None = Field(default=None, max_length=100)

    image_url: str | None = None

    is_active: bool | None = None
    status: str | None = None

    # Publicado en el catálogo de clientes (además de estar activo y con su
    # categoría pública). La distribuidora lo elige producto por producto.
    is_public: bool = True

    # -------------------------
    # VALIDATORS COMPARTIDOS
    # -------------------------

    @field_validator(
        "name",
        "brand",
        "category",
        "currency",
        "sku",
        mode="before",
        check_fields=False,
    )
    @classmethod
    def strip_basic_text_fields(cls, value):
        if value is None:
            return value

        if isinstance(value, str):
            cleaned = " ".join(value.strip().split())
            return cleaned or None

        return value

    @field_validator("description", mode="before")
    @classmethod
    def strip_optional_text_fields(cls, value):
        if value is None:
            return None

        if isinstance(value, str):
            cleaned = " ".join(value.strip().split())
            return cleaned or None

        return value

    @field_validator("slug", mode="before")
    @classmethod
    def strip_slug(cls, value):
        if value is None:
            return None

        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None

        return value

    @field_validator("image_url", mode="after")
    @classmethod
    def stringify_image_url(cls, value):
        if value is None:
            return None

        return str(value)

# =========================================
# CREACIÓN MANUAL ADMIN
# =========================================

class ProductCreateAdmin(ProductBase):
    # Precio de venta: o se manda `unit_price` o se elige un % de remarque sobre el costo
    # (`markup_percent`) y el precio se calcula y se redondea al peso entero:
    # costo 200 + 40% = 280 · 400,50 -> 401. Si vienen los dos, manda el remarque.
    unit_price: Decimal | None = Field(default=None, ge=0)
    markup_percent: Decimal | None = Field(default=None, ge=0, le=10_000)

    # Vencimiento del stock inicial (necesita stock_current > 0 para quedar en el historial).
    expiry_date: date | None = None

    @model_validator(mode="after")
    def _resolve_sale_price(self):
        if self.markup_percent is not None:
            self.unit_price = price_from_markup(self.unit_cost, self.markup_percent)
        elif self.unit_price is None:
            raise ValueError("Ingresá el precio de venta o un % de remarque sobre el costo")
        return self

    brand: str | None = Field(default=None, max_length=100)
    # Lo normal: elegir una categoría ya creada (category_id). `category` (texto)
    # queda para importaciones: se busca por nombre y, si no existe, se crea privada.
    category_id: int | None = Field(default=None, gt=0)
    category: str | None = Field(default=None, max_length=100)
    image_url: str | None = None

# =========================================
# CREACIÓN BORRADOR
# IMPORT / REMITOS
# =========================================

class ProductCreateDraft(ProductBase):
    brand: str | None = Field(default=None, max_length=100)
    category_id: int | None = Field(default=None, gt=0)
    category: str | None = Field(default=None, max_length=100)
    image_url: str | None = None

class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    brand: str | None = Field(default=None, min_length=1, max_length=100)
    category_id: int | None = Field(default=None, gt=0)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    unit_cost: Decimal | None = Field(default=None, ge=0)
    unit_price: Decimal | None = Field(default=None, ge=0)
    # Si se manda sin `unit_price`, el precio se recalcula: costo + remarque (redondeado).
    markup_percent: Decimal | None = Field(default=None, ge=0, le=10_000)
    currency: str | None = Field(default=None, min_length=1, max_length=10)
    stock_current: int | None = Field(default=None, ge=0)
    stock_min: int | None = Field(default=None, ge=0)
    image_url: str | None = None
    status: str | None = None
    is_active: bool | None = None
    is_public: bool | None = None

    @field_validator(
        "name",
        "brand",
        "category",
        "currency",
        mode="before",
    )
    @classmethod
    def strip_basic_text_fields(cls, value):
        if value is None:
            return value

        if isinstance(value, str):
            cleaned = " ".join(value.strip().split())
            return cleaned or None

        return value

    @field_validator("description", mode="before")
    @classmethod
    def strip_optional_text_fields(cls, value):
        if value is None:
            return None

        if isinstance(value, str):
            cleaned = " ".join(value.strip().split())
            return cleaned or None

        return value

    @field_validator("slug", mode="before")
    @classmethod
    def strip_slug(cls, value):
        if value is None:
            return None

        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None

        return value

    @field_validator("image_url", mode="after")
    @classmethod
    def stringify_image_url(cls, value):
        if value is None:
            return None

        return str(value)

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None
    brand: str | None
    brand_normalized: str | None
    category_id: int | None = None
    category: str | None
    category_normalized: str | None
    slug: str
    unit_cost: Decimal
    unit_price: Decimal
    markup_percent: Decimal | None = None
    currency: str
    stock_current: int
    stock_min: int
    sku: str | None
    image_url: str | None
    is_active: bool
    is_public: bool = True
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int


# =========================================
# VISTA DE LA TIENDA (visitantes y clientes)
# =========================================
# Lo que ve quien NO es personal de la distribuidora. A propósito no incluye el
# costo (unit_cost), el stock mínimo, el estado interno ni los campos normalizados.

class PublicProductResponse(BaseModel):
    id: int
    name: str
    description: str | None
    brand: str | None
    category_id: int | None = None
    category: str | None
    slug: str
    unit_price: Decimal
    currency: str
    stock_current: int
    sku: str | None
    image_url: str | None

    model_config = ConfigDict(from_attributes=True)

class PublicProductListResponse(BaseModel):
    items: list[PublicProductResponse]
    total: int
    page: int
    page_size: int

class ProductFiltersResponse(BaseModel):
    brands: list[str]
    categories: list[str]
