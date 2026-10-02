from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixin_model import TenantMixin

if TYPE_CHECKING:
    from app.models.client_model import Client
    from app.models.supplier_model import Supplier
    from app.models.sales_rep_model import SalesRep

class Check(Base, TenantMixin):
    """
    Cheque físico recibido de un cliente (cobro) o emitido a un proveedor
    (pago). Se registra como 'pendiente' y NO afecta el saldo de cuenta
    corriente hasta que se marca como 'acreditado': recién ahí se genera
    el ClientAccountMovement/SupplierAccountMovement real (vía
    ClientAccountMovementService.register_payment /
    SupplierAccountMovementService.register_payment), reusando la misma
    lógica que un cobro/pago instantáneo.

    Si se marca como 'rechazado', no hay nada que revertir: como el saldo
    nunca se tocó, el remito/cuenta corriente sigue como si el cheque no
    hubiese existido.
    """
    __tablename__ = "checks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 'received' (cobro a cliente) | 'issued' (pago a proveedor)
    direction: Mapped[str] = mapped_column(String(10), nullable=False, index=True)

    check_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    bank_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    drawer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Fecha en la que se libró el cheque.
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    # Fecha a partir de la cual es cobrable (== issue_date si es "a la
    # vista"; posterior si es un cheque diferido).
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    # Fecha límite para depositarlo/presentarlo (se carga siempre a mano).
    due_date: Mapped[date] = mapped_column(Date, nullable=False)

    # 'pendiente' | 'depositado' | 'acreditado' | 'rechazado'
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pendiente",
        server_default="pendiente",
        index=True,
    )

    client_id: Mapped[int | None] = mapped_column(
        ForeignKey("clients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Imputaciones pendientes (lista de {document_type, invoice_id,
    # amount}, mismo formato que ClientPaymentAllocationItem /
    # PaymentAllocationItem) a aplicar recién cuando se acredite.
    pending_allocations: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Se completan al acreditar: el movimiento de cuenta corriente que
    # este cheque terminó generando.
    client_account_movement_id: Mapped[int | None] = mapped_column(
        ForeignKey("client_account_movements.id", ondelete="SET NULL"),
        nullable=True,
    )
    supplier_account_movement_id: Mapped[int | None] = mapped_column(
        ForeignKey("supplier_account_movements.id", ondelete="SET NULL"),
        nullable=True,
    )

    deposited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("sales_reps.id"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    client: Mapped["Client | None"] = relationship("Client")
    supplier: Mapped["Supplier | None"] = relationship("Supplier")
    creator: Mapped["SalesRep | None"] = relationship("SalesRep")

    __table_args__ = (
        CheckConstraint(
            "direction IN ('received', 'issued')",
            name="ck_check_direction",
        ),
        CheckConstraint(
            "status IN ('pendiente', 'depositado', 'acreditado', 'rechazado')",
            name="ck_check_status",
        ),
        CheckConstraint(
            "(direction = 'received' AND client_id IS NOT NULL AND supplier_id IS NULL) "
            "OR (direction = 'issued' AND supplier_id IS NOT NULL AND client_id IS NULL)",
            name="ck_check_direction_matches_owner",
        ),
        CheckConstraint("amount > 0", name="ck_check_amount_positive"),
    )
