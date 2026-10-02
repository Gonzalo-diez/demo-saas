from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class ClientBranchBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    address: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)

    lat: Decimal | None = Field(default=None, ge=-90, le=90)
    lng: Decimal | None = Field(default=None, ge=-180, le=180)

    contact_name: str | None = Field(default=None, max_length=255)
    contact_phone: str | None = Field(default=None, max_length=50)
    reference: str | None = Field(default=None, max_length=255)

    is_main: bool = False
    is_active: bool = True

    # 🔥 VALIDACIÓN CLAVE
    @model_validator(mode="after")
    def validate_lat_lng(self):
        if (self.lat is None) != (self.lng is None):
            raise ValueError("lat y lng deben venir juntos")
        return self

class ClientBranchCreate(ClientBranchBase):
    pass

class ClientBranchUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    address: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)

    lat: Decimal | None = Field(default=None, ge=-90, le=90)
    lng: Decimal | None = Field(default=None, ge=-180, le=180)

    contact_name: str | None = Field(default=None, max_length=255)
    contact_phone: str | None = Field(default=None, max_length=50)
    reference: str | None = Field(default=None, max_length=255)

    is_main: bool | None = None
    is_active: bool | None = None

    # 🔥 MISMA VALIDACIÓN EN UPDATE
    @model_validator(mode="after")
    def validate_lat_lng(self):
        if (self.lat is None) != (self.lng is None):
            raise ValueError("lat y lng deben venir juntos")
        return self

class ClientBranchResponse(ClientBranchBase):
    id: int
    client_id: int
    h3_index: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ClientBranchListResponse(BaseModel):
    branches: list[ClientBranchResponse]