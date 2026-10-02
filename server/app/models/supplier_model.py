from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, Numeric, String, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.supplier_account_movement_model import SupplierAccountMovement

class Supplier(Base, TenantMixin):
    __tablename__ = "suppliers"
    
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "tax_id",
            name="uq_suppliers_tenant_tax_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    # Saldo cacheado de cuenta corriente (positivo = nosotros le debemos al proveedor).
    # Fuente de verdad real es el ledger en SupplierAccountMovement; este campo
    # se mantiene sincronizado en la misma transacción para lecturas rápidas.
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    purchase_invoices = relationship(
        "PurchaseInvoice",
        back_populates="supplier",
    )
    purchase_quotes = relationship(
        "PurchaseQuote",
        back_populates="supplier",
    )
    account_movements: Mapped[list["SupplierAccountMovement"]] = relationship(
        "SupplierAccountMovement",
        back_populates="supplier",
    )