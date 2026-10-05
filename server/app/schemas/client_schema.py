from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from datetime import datetime
from app.schemas.client_branch_schema import (
    ClientBranchCreate, 
    ClientBranchResponse, 
    ClientBranchUpdate
)
from app.utils.formatters import normalize_email, normalize_phone

class MessageResponse(BaseModel):
    message: str

class ClientLogin(BaseModel):
    email: str
    password: str = Field(..., min_length=1, max_length=255)
    # Distribuidora a la que se quiere entrar (alternativa al header X-Tenant-Slug).
    tenant_slug: str | None = Field(default=None, max_length=100)
    
    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v):
        if isinstance(v, str):
            return v.strip().lower()
        return v
    

class ClientRegister(BaseModel):
    """
    Alta de un cliente desde la tienda pública (autoregistro): se pide recién
    cuando el visitante va a finalizar una compra.
    """
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=255)
    phone: str = Field(..., min_length=5, max_length=50)
    tax_id: str | None = Field(default=None, min_length=1, max_length=50)
    client_type: Literal["individual", "company"] = "individual"
    # Distribuidora (alternativa a los headers X-Tenant-Domain / X-Tenant-Slug).
    tenant_slug: str | None = Field(default=None, max_length=100)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v):
        if isinstance(v, str):
            return " ".join(v.strip().split())
        return v

    @field_validator("email", mode="before")
    @classmethod
    def lower_email(cls, v):
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("phone", mode="before")
    @classmethod
    def clean_phone(cls, v):
        return normalize_phone(v)


class ClientSalesRepSummary(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)

class ClientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    tax_id: str | None = Field(default=None, min_length=1, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    client_type: str = Field(default="company", min_length=1, max_length=50)
    is_active: bool = True
    
    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        if isinstance(v, str):
            return " ".join(v.strip().split())
        return v
    
    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        return normalize_email(v)
    
    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        return normalize_phone(v)

class ClientCreate(ClientBase):
    password: str = Field(..., min_length=6, max_length=255)
    branches: list[ClientBranchCreate] = Field(default_factory=list)

class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    tax_id: str | None = Field(default=None, min_length=1, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    client_type: str | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=6, max_length=255)
    branches: list[ClientBranchUpdate] | None = None
    
    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        if isinstance(v, str):
            return " ".join(v.strip().split())
        return v
    
    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        return normalize_email(v)
    
    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        return normalize_phone(v)

class ClientResponse(ClientBase):
    id: int
    sales_rep_id: int | None = None
    current_balance: Decimal = Decimal("0.00")
    created_at: datetime
    updated_at: datetime
    branches: list[ClientBranchResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}

class ClientListResponse(BaseModel):
    clients: list[ClientResponse] = Field(default_factory=list)
    total: int
    page: int
    page_size: int
    total_pages: int