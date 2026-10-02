from decimal import Decimal
from typing import Any, List, Literal
from pydantic import BaseModel, ConfigDict, Field, AnyHttpUrl, field_validator
from app.utils.category_normalizer import resolve_category_value

class ProductImportRow(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    brand: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=100)
    unit_cost: Decimal = Field(..., ge=0)
    unit_price: Decimal = Field(..., ge=0)
    stock_current: int = Field(default=0, ge=0)
    stock_min: int = Field(default=0, ge=0)
    image_url: str | None = None
    is_active: bool | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("sku", "name", "brand", mode="before")
    @classmethod
    def strip_strings(cls, v: Any) -> Any:
        if isinstance(v, str):
            return " ".join(v.strip().split())
        return v

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category_field(cls, v: Any) -> str:
        return resolve_category_value(str(v)) if v else v

    @field_validator("image_url", mode="before")
    @classmethod
    def stringify_url(cls, v: str | None) -> str | None:
        if v is None:
            return None

        value = str(v).strip()

        if not value:
            return None

        if value.lower() in {
            "nan",
            "none",
            "null",
            "n/a",
            "-"
        }:
            return None

        return value

class ProductImportRowError(BaseModel):
    row_number: int
    data: dict[str, Any]
    errors: List[str]

class ProductImportPreviewResponse(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    rows_valid: List[ProductImportRow]
    rows_invalid: List[ProductImportRowError]

class ProductImportCommitRequest(BaseModel):
    rows: List[ProductImportRow]
    mode: Literal["upsert", "create", "update"] = "upsert"

class ProductImportCommitResponse(BaseModel):
    total: int
    created: int
    updated: int
    failed: int
    errors: List[str] = Field(default_factory=list)