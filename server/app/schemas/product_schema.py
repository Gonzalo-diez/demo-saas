from decimal import Decimal
from datetime import datetime
from typing import Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)
from app.utils.category_normalizer import resolve_category_value

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

    @field_validator("category", mode="before", check_fields=False)
    @classmethod
    def normalize_category(cls, value):
        if value is None:
            return value

        return resolve_category_value(str(value))

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
    brand: str | None = Field(default=None, max_length=100)
    category: str | None = Field(default=None, max_length=100)
    image_url: str | None = None

# =========================================
# CREACIÓN BORRADOR
# IMPORT / REMITOS
# =========================================

class ProductCreateDraft(ProductBase):
    brand: str | None = Field(default=None, max_length=100)
    category: str | None = Field(default=None, max_length=100)
    image_url: str | None = None

class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    brand: str | None = Field(default=None, min_length=1, max_length=100)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    unit_cost: Decimal | None = Field(default=None, ge=0)
    unit_price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=1, max_length=10)
    stock_current: int | None = Field(default=None, ge=0)
    stock_min: int | None = Field(default=None, ge=0)
    image_url: str | None = None
    status: str | None = None
    is_active: bool | None = None

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

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, value):
        if value is None:
            return value

        return resolve_category_value(str(value))

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
    category: str | None
    category_normalized: str | None
    slug: str
    unit_cost: Decimal
    unit_price: Decimal
    currency: str
    stock_current: int
    stock_min: int
    sku: str | None
    image_url: str | None
    is_active: bool
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int

class ProductFiltersResponse(BaseModel):
    brands: list[str]
    categories: list[str]


class CategoryOption(BaseModel):
    value: str
    label: str


class ProductCategoriesResponse(BaseModel):
    """Opciones de categoría para el alta/edición manual de productos (admin)."""

    # Categorías seteadas: se muestran en el catálogo online.
    catalog: list[CategoryOption]
    # Categorías libres ya usadas por productos: solo venta B2B.
    free: list[str]
    # alias normalizado -> categoría canónica de catálogo (detección de colisiones).
    catalog_aliases: dict[str, str]