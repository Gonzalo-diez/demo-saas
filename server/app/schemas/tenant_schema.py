from __future__ import annotations

from datetime import datetime
from math import ceil
import re
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _normalize_slug(value):
    if value is None:
        return value
    value = str(value).strip().lower()
    if not _SLUG_RE.match(value):
        raise ValueError(
            "El slug solo puede tener minúsculas, números y guiones (ej: 'mi-distribuidora')"
        )
    return value


class TenantBase(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=100)
    logo_url: str | None = Field(default=None, max_length=500)
    email: EmailStr | None = Field(default=None, max_length=255)
    is_active: bool = True

    @field_validator("slug", mode="after")
    @classmethod
    def _validate_slug(cls, v):
        return _normalize_slug(v)


class TenantCreate(TenantBase):
    pass


class TenantProvision(TenantCreate):
    """
    Alta de una distribuidora nueva. Opcionalmente crea en el mismo paso su
    primer usuario administrador (superusuario del tenant).
    """
    admin_name: str | None = Field(default=None, max_length=255)
    admin_email: EmailStr | None = None
    admin_password: str | None = Field(default=None, min_length=6, max_length=255)

    @model_validator(mode="after")
    def _admin_fields_together(self):
        if (self.admin_email is None) != (self.admin_password is None):
            raise ValueError("admin_email y admin_password deben enviarse juntos")
        return self


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    slug: str | None = Field(default=None, max_length=100)
    logo_url: str | None = Field(default=None, max_length=500)
    email: EmailStr | None = Field(default=None, max_length=255)
    is_active: bool | None = None

    @field_validator("slug", mode="after")
    @classmethod
    def _validate_slug(cls, v):
        return _normalize_slug(v)


class TenantPublicResponse(BaseModel):
    """Datos mínimos y no sensibles de una distribuidora (pantalla de login / branding)."""
    id: int
    name: str
    slug: str
    logo_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TenantResponse(TenantBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
class PaginatedTenantResponse(BaseModel):
    items: list[TenantResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(cls, items: list, total: int, page: int, page_size: int):
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if page_size > 0 else 0,
        )