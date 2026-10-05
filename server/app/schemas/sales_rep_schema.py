from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.utils.formatters import normalize_email, normalize_phone

class SalesRepLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=255)
    # Distribuidora a la que se quiere entrar (alternativa al header X-Tenant-Slug).
    tenant_slug: str | None = Field(default=None, max_length=100)
    
    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v):
        if isinstance(v, str):
            return v.strip().lower()
        return v

class SalesRepBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)
    home_lat: float | None = Field(default=None, ge=-90, le=90)
    home_lng: float | None = Field(default=None, ge=-180, le=180)
    coverage_radius_km: float | None = Field(default=None, gt=0)
    is_active: bool = True
    
    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: Any) -> Any:
        if isinstance(v, str):
            return " ".join(v.strip().split())
        return v
    
    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v):
        return normalize_email(v)

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, v: Any) -> Any:
        return normalize_phone(v)

class SalesRepCreate(SalesRepBase):
    password: str = Field(..., min_length=6, max_length=255)
    is_superuser: bool = False

class SalesRepUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None
    is_superuser: bool | None = None
    home_lat: float | None = Field(default=None, ge=-90, le=90)
    home_lng: float | None = Field(default=None, ge=-180, le=180)
    coverage_radius_km: float | None = Field(default=None, gt=0)
    password: str | None = Field(default=None, min_length=6)
    
    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: Any) -> Any:
        if isinstance(v, str):
            return " ".join(v.strip().split())
        return v
    
    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v):
        return normalize_email(v)

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, v: Any) -> Any:
        return normalize_phone(v)

class SalesRepResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str | None
    is_active: bool
    is_superuser: bool
    home_lat: float | None
    home_lng: float | None
    coverage_radius_km: float | None
    home_h3_index: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
class SalesRepListResponse(BaseModel):
    sales_reps: list[SalesRepResponse] = Field(default_factory=list)
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)
    
class ChangePasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=255)

class MessageResponse(BaseModel):
    message: str