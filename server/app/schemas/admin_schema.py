from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from app.utils.formatters import normalize_email


class AdminLogin(BaseModel):
    email: EmailStr
    password: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: Any):
        return normalize_email(value)


class AdminCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=6,
        max_length=255,
    )

    is_active: bool = True

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: Any):
        if isinstance(value, str):
            return " ".join(value.strip().split())
        return value

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: Any):
        return normalize_email(value)


class AdminUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    email: EmailStr | None = None

    password: str | None = Field(
        default=None,
        min_length=6,
        max_length=255,
    )

    is_active: bool | None = None

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: Any):
        if isinstance(value, str):
            return " ".join(value.strip().split())
        return value

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: Any):
        return normalize_email(value)


class AdminResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class AdminLoginResponse(BaseModel):
    admin: AdminResponse


class MessageResponse(BaseModel):
    message: str