from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _clean_name(value: Any) -> Any:
    if isinstance(value, str):
        return " ".join(value.strip().split())
    return value


def _clean_image_url(value: Any) -> Any:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    # Imagen de la categoría. Obligatoria si la categoría es pública.
    image_url: str | None = None
    # Visible para los clientes en el catálogo. Si es False, sus productos quedan
    # solo para venta B2B interna.
    is_public: bool = True
    # Los pedidos online con productos de esta categoría piden DNI + mayoría de edad.
    requires_age_verification: bool = False

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, v):
        return _clean_name(v)

    @field_validator("description", mode="before")
    @classmethod
    def clean_description(cls, v):
        v = _clean_name(v)
        return v or None

    @field_validator("image_url", mode="before")
    @classmethod
    def clean_image_url(cls, v):
        return _clean_image_url(v)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    image_url: str | None = None
    is_public: bool | None = None
    requires_age_verification: bool | None = None

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, v):
        return _clean_name(v)

    @field_validator("description", mode="before")
    @classmethod
    def clean_description(cls, v):
        v = _clean_name(v)
        return v or None

    @field_validator("image_url", mode="before")
    @classmethod
    def clean_image_url(cls, v):
        return _clean_image_url(v)


class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    image_url: str | None = None
    is_public: bool
    requires_age_verification: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryAdminResponse(CategoryResponse):
    """Vista del panel de la distribuidora: incluye cuántos productos tiene."""
    product_count: int = 0


class CategoryListResponse(BaseModel):
    items: list[CategoryAdminResponse]
    total: int
