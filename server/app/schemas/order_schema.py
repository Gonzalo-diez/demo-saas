from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator
from app.utils.formatters import normalize_phone, normalize_email

OrderStatus = Literal[
    "pending_confirmation",
    "confirmed",
    "preparing",
    "shipped",
    "delivered",
    "cancelled",
]

DeliveryType = Literal["delivery", "pickup"]
# Documento de venta que se genera al pasar a 'preparing'.
DocumentType = Literal["sales_invoice", "sales_quote"]
OrderType = Literal["ONLINE", "B2B"]

PersonType = Literal["individual", "empresa"]
IvaCondition = Literal[
    "consumidor_final",
    "responsable_inscripto",
    "monotributista",
    "exento",
]

class OrderItemBase(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name_snapshot: str
    product_brand_snapshot: str | None = None
    product_sku_snapshot: str | None = None
    product_image_url_snapshot: str | None = None
    quantity: int

    unit_price: Decimal
    subtotal: Decimal

    # SOLO B2B
    unit_cost: Decimal | None = None
    subtotal_cost: Decimal | None = None
    margin_amount: Decimal | None = None

    model_config = ConfigDict(from_attributes=True)

class OrderSalesRepSummary(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)

class OrderClientSummary(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class OrderClientBranchSummary(BaseModel):
    id: int
    client_id: int
    name: str
    address: Optional[str] = None
    city: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class OrderCreateBase(BaseModel):
    currency: str = Field(default="ARS", min_length=3, max_length=10)
    # Remito de venta (default) o presupuesto de venta.
    document_type: DocumentType = "sales_invoice"
    items: list[OrderItemCreate] = Field(..., min_length=1)

class OrderCreateShop(OrderCreateBase):
    sales_type: Literal["ONLINE"] = "ONLINE"

    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_phone: str = Field(..., min_length=5, max_length=50)
    customer_email: EmailStr

    # Sucursal del cliente logueado a la que corresponde el pedido
    # (opcional: no todos los clientes tienen sucursales cargadas).
    # Se valida en el service que pertenezca al cliente autenticado.
    client_branch_id: Optional[int] = Field(default=None, gt=0)

    delivery_type: DeliveryType = "delivery"
    delivery_address: str
    delivery_city: str
    delivery_reference: Optional[str] = None
    preferred_delivery_date: date

    # Verificación de identidad (obligatoria solo si el carrito tiene
    # productos regulados, ej: tabaco — validado en el service, no acá,
    # porque acá no tenemos acceso al catálogo de productos).
    customer_dni: Optional[str] = Field(default=None, min_length=6, max_length=20)
    age_confirmed: bool = False

    # Datos fiscales (opcionales; si el CUIT coincide con un cliente B2B
    # existente, el pedido queda vinculado y se remito como tal).
    customer_tax_id: Optional[str] = Field(default=None, min_length=8, max_length=20)
    customer_person_type: Optional[PersonType] = None
    customer_iva_condition: Optional[IvaCondition] = None

    @field_validator("customer_dni", "customer_tax_id", mode="before")
    @classmethod
    def strip_identity_numbers(cls, v):
        if not isinstance(v, str):
            return v
        digits = "".join(ch for ch in v if ch.isdigit())
        return digits or None

    @field_validator("customer_name", "currency", mode="before")
    @classmethod
    def strip_text(cls, v):
        return " ".join(v.strip().split()) if isinstance(v, str) else v
    
    @field_validator("customer_email", mode="before")
    @classmethod
    def validate_email(cls, v):
        return normalize_email(v)

    @field_validator("customer_phone", mode="before")
    @classmethod
    def validate_phone(cls, v):
        return normalize_phone(v)

    @model_validator(mode="after")
    def validate_logic(self):
        if self.delivery_type == "delivery":
            if not self.delivery_address or not self.delivery_city:
                raise ValueError("Dirección y ciudad son obligatorias para delivery")

        product_ids = [i.product_id for i in self.items]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("No se permiten productos duplicados")
        
        if self.preferred_delivery_date < date.today():
            raise ValueError(
                "La fecha de entrega no puede ser en el pasado"
            )

        if self.preferred_delivery_date > date.today() + timedelta(days=30):
            raise ValueError(
                "La fecha de entrega es demasiado lejana"
            )

        return self

class OrderCreateB2B(OrderCreateBase):
    sales_type: Literal["B2B"] = "B2B"

    client_id: int = Field(..., gt=0)
    client_branch_id: int | None = Field(default=None, gt=0)
    
class OrderItemUpdate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    
class OrderEditBase(BaseModel):
    items: list[OrderItemCreate] = Field(..., min_length=1)
    
class OrderEditShop(OrderEditBase):
    customer_name: str | None = Field(default=None, min_length=1, max_length=255)
    customer_phone: str | None = Field(default=None, min_length=5, max_length=50)
    customer_email: EmailStr | None = None

    delivery_type: DeliveryType | None = None
    delivery_address: str | None = None
    delivery_city: str | None = None
    delivery_reference: str | None = None
    preferred_delivery_date: date | None = None
    
    @field_validator("preferred_delivery_date")
    @classmethod
    def validate_delivery_date(cls, value):
        if value is None:
            return value

        if value < date.today():
            raise ValueError(
                "La fecha de entrega no puede ser en el pasado"
            )

        if value > date.today() + timedelta(days=30):
            raise ValueError(
                "La fecha de entrega es demasiado lejana"
            )

        return value
    
class OrderEditB2B(OrderEditBase):
    client_branch_id: int | None = Field(default=None, gt=0)
    delivery_reference: str | None = None

class OrderUpdateShop(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    delivery_address: Optional[str] = None
    delivery_city: Optional[str] = None
    delivery_type: DeliveryType | None = None
    delivery_reference: str | None = None
    # Solo se puede cambiar mientras no se haya generado el documento.
    document_type: DocumentType | None = None

class OrderUpdateB2B(BaseModel):
    client_branch_id: int | None = Field(default=None, gt=0)
    document_type: DocumentType | None = None

class OrderUpdateStatus(BaseModel):
    status: OrderStatus
    
class OrderScheduleDelivery(BaseModel):
    scheduled_delivery_date: date

class OrderSalesInvoiceSummary(BaseModel):
    id: int
    invoice_number: str
    invoice_date: date
    status: str

    model_config = ConfigDict(from_attributes=True)

class OrderSalesQuoteSummary(BaseModel):
    id: int
    quote_number: str
    quote_date: date
    status: str

    model_config = ConfigDict(from_attributes=True)

class OrderResponse(BaseModel):
    id: int
    sales_type: OrderType
    status: OrderStatus
    # Nombre histórico: significa "documento de venta generado" (remito o presupuesto).
    invoice_generated: bool
    document_type: DocumentType = "sales_invoice"

    customer_name: str | None = None
    customer_phone: str | None = None
    customer_email: EmailStr | None = None

    customer_dni: str | None = None
    age_confirmed: bool = False
    customer_tax_id: str | None = None
    customer_person_type: PersonType | None = None
    customer_iva_condition: IvaCondition | None = None

    delivery_type: DeliveryType | None = None
    delivery_address: str | None = None
    delivery_city: str | None = None
    delivery_reference: str | None = None
    
    preferred_delivery_date: date | None = None
    scheduled_delivery_date: date | None = None
    delivered_at: datetime | None = None

    client_id: int | None = None
    client_branch_id: int | None = None
    sales_rep_id: int | None = None

    client: OrderClientSummary | None = None
    client_branch: OrderClientBranchSummary | None = None
    sales_rep: OrderSalesRepSummary | None = None
    
    sales_invoice: OrderSalesInvoiceSummary | None = None
    sales_quote: OrderSalesQuoteSummary | None = None

    total_amount: Decimal
    total_cost: Decimal | None = None
    margin_amount: Decimal | None = None
    currency: str

    items: list[OrderItemResponse] = Field(default_factory=list)

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
class OrderItemPublicResponse(BaseModel):
    id: int
    product_id: int
    product_name_snapshot: str
    product_brand_snapshot: str | None = None
    product_sku_snapshot: str | None = None
    product_image_url_snapshot: str | None = None
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderPublicResponse(BaseModel):
    id: int
    status: OrderStatus

    customer_name: str | None = None
    customer_phone: str | None = None
    customer_email: EmailStr | None = None

    delivery_type: DeliveryType | None = None
    delivery_address: str | None = None
    delivery_city: str | None = None
    delivery_reference: str | None = None

    preferred_delivery_date: date | None = None

    total_amount: Decimal
    currency: str

    items: list[OrderItemPublicResponse] = Field(default_factory=list)

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int