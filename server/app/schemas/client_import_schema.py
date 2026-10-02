from typing import Literal, List, Any
from pydantic import BaseModel, Field, model_validator, field_validator
from app.utils.formatters import normalize_phone, normalize_email

class ClientImportRow(BaseModel):
    # Client
    client_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )
    email: str | None = Field(
        default=None,
        max_length=255,
    )
    tax_id: str | None = Field(
        default=None,
        max_length=50,
    )
    client_type: str = Field(
        default="company",
        max_length=50,
    )
    password: str | None = Field(
        default=None,
        max_length=255,
    )
    is_active: bool = True

    # Branch
    branch_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )
    address: str | None = Field(
        default=None,
        max_length=255,
    )
    city: str | None = Field(
        default=None,
        max_length=100,
    )
    lat: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )
    lng: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )
    contact_name: str | None = Field(
        default=None,
        max_length=255,
    )
    contact_phone: str | None = Field(
        default=None,
        max_length=50,
    )
    reference: str | None = Field(
        default=None,
        max_length=255,
    )
    is_main: bool = False
    branch_is_active: bool = True
    
    @field_validator(
        "contact_phone",
        mode="before",
    )
    @classmethod
    def validate_contact_phone(cls, value):
        return normalize_phone(value)
    
    @field_validator(
        "email",
        mode="before",
    )
    @classmethod
    def validate_email(cls, value):
        return normalize_email(value) if value else None

    @field_validator(
        "client_name",
        mode="before",
    )
    @classmethod
    def validate_client_name(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator(
        "password",
        mode="before",
    )
    @classmethod
    def validate_password(cls, value):
        if value is None or value == "":
            return None
        value = str(value).strip()
        if len(value) < 6:
            raise ValueError(
                "La contraseña debe tener al menos 6 caracteres (o dejarla "
                "vacía para generarla automáticamente al crear el cliente)"
            )
        return value

    @model_validator(mode="after")
    def validate_lat_lng(self):
        if (self.lat is None) != (self.lng is None):
            raise ValueError(
                "lat y lng deben venir juntos"
            )
        return self
    
class ClientImportRowError(BaseModel):
    row_number: int
    data: dict[str, Any]
    errors: List[str]

class ClientImportPreviewItem(BaseModel):
    row_number: int
    client_name: str
    branch_name: str
    client_action: Literal[
        "create",
        "update",
        "skip",
        "error",
    ]
    branch_action: Literal[
        "create",
        "update",
        "skip",
        "error",
    ]

    errors: list[str] = Field(
        default_factory=list
    )

class ClientImportPreviewResponse(BaseModel):
    total_rows: int
    clients_to_create: int = 0
    clients_to_update: int = 0
    branches_to_create: int = 0
    branches_to_update: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    skipped_rows: int = 0

    items: list[
        ClientImportPreviewItem
    ] = Field(default_factory=list)

    rows_valid: List[ClientImportRow]
    rows_invalid: List[ClientImportRowError]
    
class ClientImportCommitRequest(BaseModel):
    rows: List[ClientImportRow]
    mode: Literal["upsert", "create", "update"] = "upsert"

class ClientImportCommitResponse(BaseModel):
    clients_created: int = 0
    clients_updated: int = 0
    branches_created: int = 0
    branches_updated: int = 0
    skipped_rows: int = 0
    generated_passwords: list["GeneratedClientPassword"] = Field(
        default_factory=list
    )

class GeneratedClientPassword(BaseModel):
    client_name: str
    email: str | None = None
    password: str