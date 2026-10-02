from typing import Any, List, Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)
from app.utils.formatters import normalize_phone, normalize_email

class SalesRepImportRow(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)
    home_lat: float | None = Field(default=None, ge=-90, le=90)
    home_lng: float | None = Field(default=None, ge=-180, le=180)
    coverage_radius_km: float | None = Field(default=None, gt=0)
    is_active: bool = True
    is_superuser: bool = False
    password: str = Field(..., min_length=6, max_length=255)
    model_config = ConfigDict(from_attributes=True)
    
    @model_validator(mode="after")
    def validate_location_fields(self):
        missing = []

        if self.home_lat is None:
            missing.append("home_lat")

        if self.home_lng is None:
            missing.append("home_lng")

        if self.coverage_radius_km is None:
            missing.append("coverage_radius_km")

        if missing:
            raise ValueError(
                f"Campos obligatorios faltantes: {', '.join(missing)}"
            )

        return self

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

class SalesRepImportRowError(BaseModel):
    row_number: int
    data: dict[str, Any]
    errors: List[str]
    
class SalesRepImportPreviewResponse(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int

    rows_valid: List[SalesRepImportRow]
    rows_invalid: List[SalesRepImportRowError]
    
class SalesRepImportCommitRequest(BaseModel):
    rows: List[SalesRepImportRow]
    mode: Literal["create", "upsert"] = "create"
    
class SalesRepImportCommitResponse(BaseModel):
    total: int
    created: int
    updated: int
    failed: int
    errors: List[str] = Field(default_factory=list)