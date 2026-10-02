from __future__ import annotations
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from app.utils.formatters import normalize_email, normalize_phone, normalize_tax_id

class SupplierImportRow(BaseModel):
    name: str = Field(..., min_length=2)
    tax_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    
    @field_validator("tax_id", mode="before")
    @classmethod
    def validate_tax_id(cls, value):
        return normalize_tax_id(value)
    
    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value):
        return normalize_email(value)
    
    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, value):
        return normalize_phone(value)

    @field_validator(
        "name",
        "address",
        mode="before",
    )
    @classmethod
    def clean_strings(cls, value):
        if value is None:
            return None

        value = str(value).strip()

        if not value:
            return None

        if value.lower() in {
            "nan",
            "none",
            "null",
            "n/a",
            "-",
        }:
            return None

        return value

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if not value:
            raise ValueError(
                "El nombre del proveedor es obligatorio."
            )

        return value
    
class SupplierImportRowError(BaseModel):
    row_number: int
    data: dict
    errors: list[str]

class SupplierImportCommitRequest(BaseModel):
    rows: List[SupplierImportRow]
    mode: Literal["create", "upsert"] = "create"

class SupplierImportPreviewItem(BaseModel):
    row_number: int
    name: str
    action: str
    errors: list[str] = Field(default_factory=list)

class SupplierImportPreviewResponse(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    rows_valid: list[SupplierImportRow]
    rows_invalid: list[SupplierImportRowError]
    create_count: int
    update_count: int
    skip_count: int
    items: list[SupplierImportPreviewItem]

class SupplierImportCommitResponse(BaseModel):
    created: int
    updated: int
    skipped: int