from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.supplier_model import Supplier
    from app.models.supplier_payment_allocation_model import SupplierPaymentAllocation
    from app.models.sales_rep_model import SalesRep

class SupplierAccountMovement(Base, TenantMixin):
    __tablename__ = "supplier_account_movements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id"),
        nullable=False,
        index=True,
    )

    movement_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # 'invoice' | 'invoice_reversal' | 'payment' | 'credit_note' | 'adjustment'

    # positivo = aumenta lo que nosotros debemos al proveedor (ej: remito de compra)
    # negativo = lo reduce (ej: pago)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    balance_before: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    payment_method: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # solo aplica cuando movement_type == 'payment'

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("sales_reps.id"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    supplier: Mapped["Supplier"] = relationship(
        "Supplier",
        back_populates="account_movements",
    )
    creator: Mapped["SalesRep | None"] = relationship(
        "SalesRep",
        back_populates="supplier_account_movements",
    )
    allocations: Mapped[list["SupplierPaymentAllocation"]] = relationship(
        "SupplierPaymentAllocation",
        back_populates="movement",
    )
