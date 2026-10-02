from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator
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

class ClientMapItem(BaseModel):
    client_id: int
    client_name: str
    client_type: str
    sales_rep_id: int | None = None
    sales_rep_name: str | None = None

    tax_id: str | None = None

    branch_id: int
    branch_name: str
    branch_address: str | None = None
    branch_city: str | None = None
    branch_is_main: bool
    h3_index: str | None = None

    lat: float
    lng: float
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class ClientMapResponse(BaseModel):
    clients: list[ClientMapItem] = Field(default_factory=list)

class ClientListResponse(BaseModel):
    clients: list[ClientResponse] = Field(default_factory=list)
    total: int
    page: int
    page_size: int
    total_pages: int