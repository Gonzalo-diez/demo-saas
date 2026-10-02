import math
from datetime import date
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.constants.account_movement_constant import (
    ALLOWED_ACCOUNT_MOVEMENT_TYPES,
    ALLOWED_ACCOUNT_REFERENCE_TYPES,
    ALLOWED_PAYMENT_METHODS,
)
from app.models.supplier_account_movement_model import SupplierAccountMovement
from app.models.supplier_model import Supplier
from app.models.supplier_payment_allocation_model import SupplierPaymentAllocation
from app.models.sales_rep_model import SalesRep
from app.repositories.supplier_account_movement_repository import (
    SupplierAccountMovementRepository,
)
from app.repositories.supplier_repository import SupplierRepository
from app.repositories.purchase_invoice_repository import PurchaseInvoiceRepository
from app.schemas.account_movement_schema import (
    InvoiceReferenceSummary,
    PaymentAllocationItem,
    PaymentAllocationSummary,
    SupplierAccountMovementResponse,
    SupplierPaymentCreate,
)
from app.schemas.account_movement_stats_schema import (
    AccountAgingBucket,
    AccountAgingSummary,
    AccountBalanceHistoryPoint,
    AccountBalanceSummary,
    AccountRankingItem,
)

# Tipos que aumentan lo que nosotros debemos al proveedor
_INCREASING_TYPES = {"invoice"}
# Tipos que lo reducen
_DECREASING_TYPES = {"invoice_reversal", "payment", "credit_note"}

# Rangos de antigüedad de deuda, en días desde la fecha del remito
_AGING_RANGES: list[tuple[str, int, int | None]] = [
    ("0-30 días", 0, 30),
    ("31-60 días", 31, 60),
    ("61-90 días", 61, 90),
    ("Más de 90 días", 91, None),
]

class SupplierAccountMovementService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SupplierAccountMovementRepository(db)
        self.supplier_repo = SupplierRepository(db)
        self.purchase_invoice_repo = PurchaseInvoiceRepository(db)

    # ------------------------------------------------------------------
    # Movimientos
    # ------------------------------------------------------------------

    def apply_movement(
        self,
        *,
        supplier_id: int,
        movement_type: str,
        amount: Decimal,
        reference_type: str | None = None,
        reference_id: int | None = None,
        payment_method: str | None = None,
        notes: str | None = None,
        created_by: int | None = None,
    ) -> SupplierAccountMovement:
        if movement_type not in ALLOWED_ACCOUNT_MOVEMENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de movimiento inválido",
            )

        if movement_type == "adjustment":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Los ajustes manuales deben registrarse con apply_manual_adjustment",
            )

        if (
            reference_type is not None
            and reference_type not in ALLOWED_ACCOUNT_REFERENCE_TYPES
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de referencia inválido",
            )

        if payment_method is not None and payment_method not in ALLOWED_PAYMENT_METHODS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Método de pago inválido",
            )

        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El monto debe ser mayor a 0",
            )

        supplier = (
            self.db.query(Supplier)
            .filter(Supplier.id == supplier_id)
            .with_for_update()
            .first()
        )

        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proveedor no encontrado",
            )

        if movement_type in _INCREASING_TYPES:
            signed_amount = amount
        elif movement_type in _DECREASING_TYPES:
            signed_amount = -amount
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de movimiento inválido",
            )

        balance_before = Decimal(supplier.current_balance)
        balance_after = balance_before + signed_amount

        movement = self.repo.create_without_commit(
            {
                "supplier_id": supplier.id,
                "movement_type": movement_type,
                "amount": signed_amount,
                "balance_before": balance_before,
                "balance_after": balance_after,
                "reference_type": reference_type,
                "reference_id": reference_id,
                "payment_method": payment_method,
                "notes": notes,
                "created_by": created_by,
            }
        )

        supplier.current_balance = balance_after
        self.db.add(supplier)

        return movement

    def apply_manual_adjustment(
        self,
        *,
        supplier_id: int,
        delta_amount: Decimal,
        notes: str | None = None,
        created_by: int | None = None,
    ) -> SupplierAccountMovement:
        if delta_amount == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El ajuste no puede ser 0",
            )

        supplier = (
            self.db.query(Supplier)
            .filter(Supplier.id == supplier_id)
            .with_for_update()
            .first()
        )

        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proveedor no encontrado",
            )

        balance_before = Decimal(supplier.current_balance)
        balance_after = balance_before + delta_amount

        movement = self.repo.create_without_commit(
            {
                "supplier_id": supplier.id,
                "movement_type": "adjustment",
                "amount": delta_amount,
                "balance_before": balance_before,
                "balance_after": balance_after,
                "reference_type": "manual_adjustment",
                "reference_id": None,
                "payment_method": None,
                "notes": notes,
                "created_by": created_by,
            }
        )

        supplier.current_balance = balance_after
        self.db.add(supplier)

        return movement

    # ------------------------------------------------------------------
    # Pagos con asignación opcional a remitos puntuales
    # ------------------------------------------------------------------

    def register_payment(
        self,
        supplier_id: int,
        data: SupplierPaymentCreate,
        current_user: SalesRep | None,
    ) -> SupplierAccountMovementResponse:
        if data.payment_method == "cheque":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Los cheques no se registran como pago inmediato: usá "
                    "POST /suppliers/{supplier_id}/checks. El cheque queda "
                    "'pendiente' y recién afecta el saldo cuando se marca "
                    "como acreditado."
                ),
            )

        return self._register_payment_internal(supplier_id, data, current_user)

    def _register_payment_internal(
        self,
        supplier_id: int,
        data: SupplierPaymentCreate,
        current_user: SalesRep | None,
    ) -> SupplierAccountMovementResponse:
        """
        Igual que register_payment pero sin el bloqueo de 'cheque': lo usa
        CheckService al acreditar un cheque emitido.
        """
        movement = self.apply_movement(
            supplier_id=supplier_id,
            movement_type="payment",
            amount=data.amount,
            reference_type="payment",
            payment_method=data.payment_method,
            notes=data.notes,
            created_by=current_user.id if current_user else None,
        )

        if data.allocations:
            self._apply_payment_allocations(
                movement=movement,
                supplier_id=supplier_id,
                allocations=data.allocations,
            )

        self.db.flush()
        self.db.refresh(movement)

        return self._build_responses([movement])[0]

    def _apply_payment_allocations(
        self,
        *,
        movement: SupplierAccountMovement,
        supplier_id: int,
        allocations: list[PaymentAllocationItem],
    ) -> None:
        invoice_ids = [a.invoice_id for a in allocations]
        invoices = self.purchase_invoice_repo.get_by_ids_for_update(invoice_ids)
        invoices_by_id = {inv.id: inv for inv in invoices}

        for alloc in allocations:
            invoice = invoices_by_id.get(alloc.invoice_id)

            if not invoice:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Remito de compra #{alloc.invoice_id} no encontrado",
                )

            if invoice.supplier_id != supplier_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"El remito #{invoice.invoice_number} no pertenece a este proveedor"
                    ),
                )

            total = invoice.total_amount or Decimal("0.00")
            remaining = total - invoice.paid_amount

            if alloc.amount > remaining:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"El monto asignado al remito #{invoice.invoice_number} "
                        f"supera su saldo pendiente (${remaining})"
                    ),
                )

            invoice.paid_amount = invoice.paid_amount + alloc.amount

            if invoice.paid_amount >= total and total > 0:
                invoice.payment_status = "paid"
            elif invoice.paid_amount > 0:
                invoice.payment_status = "partial"
            else:
                invoice.payment_status = "pending"

            self.db.add(invoice)

            allocation_row = SupplierPaymentAllocation(
                supplier_account_movement_id=movement.id,
                purchase_invoice_id=invoice.id,
                amount_applied=alloc.amount,
            )
            self.db.add(allocation_row)

        self.db.flush()

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def get_by_id(self, movement_id: int) -> SupplierAccountMovementResponse:
        movement = self.repo.get_by_id(movement_id)
        if not movement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movimiento de cuenta corriente no encontrado",
            )
        return self._build_responses([movement])[0]

    def get_movements(
        self,
        page: int = 1,
        page_size: int = 20,
        supplier_id: int | None = None,
        movement_type: str | None = None,
        reference_type: str | None = None,
    ) -> dict:
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="page debe ser mayor o igual a 1",
            )

        if page_size < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="page_size debe ser mayor o igual a 1",
            )

        if supplier_id is not None:
            supplier = self.supplier_repo.get_by_id(supplier_id)
            if not supplier:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Proveedor no encontrado",
                )

        if (
            movement_type is not None
            and movement_type not in ALLOWED_ACCOUNT_MOVEMENT_TYPES
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de movimiento inválido",
            )

        if (
            reference_type is not None
            and reference_type not in ALLOWED_ACCOUNT_REFERENCE_TYPES
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de referencia inválido",
            )

        items, total = self.repo.get_movements(
            page=page,
            page_size=page_size,
            supplier_id=supplier_id,
            movement_type=movement_type,
            reference_type=reference_type,
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return {
            "items": self._build_responses(items),
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_supplier_movements(
        self,
        supplier_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        return self.get_movements(
            page=page,
            page_size=page_size,
            supplier_id=supplier_id,
        )

    # ------------------------------------------------------------------
    # Métricas
    # ------------------------------------------------------------------

    def get_balance_summary(self) -> AccountBalanceSummary:
        total_debt, total_favor, debtor_count, favor_count = (
            self.supplier_repo.get_balance_summary_row()
        )
        return AccountBalanceSummary(
            total_debt=total_debt,
            total_favor=total_favor,
            net_balance=total_debt - total_favor,
            debtor_count=debtor_count,
            favor_count=favor_count,
        )

    def get_ranking(self, limit: int = 10, order: str = "debtors") -> list[AccountRankingItem]:
        if order not in {"debtors", "favor"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="order debe ser 'debtors' o 'favor'",
            )

        suppliers = self.supplier_repo.get_top_by_balance(
            limit=limit,
            ascending=order == "favor",
        )
        return [
            AccountRankingItem(id=s.id, name=s.name, balance=s.current_balance)
            for s in suppliers
        ]

    def get_aging_summary(self) -> AccountAgingSummary:
        invoices = self.purchase_invoice_repo.get_pending_for_aging()
        today = date.today()

        buckets = {
            label: {"amount": Decimal("0.00"), "count": 0}
            for label, _, _ in _AGING_RANGES
        }
        total_pending = Decimal("0.00")

        for invoice in invoices:
            outstanding = (invoice.total_amount or Decimal("0.00")) - invoice.paid_amount
            if outstanding <= 0:
                continue

            days = (today - invoice.invoice_date).days
            for label, min_days, max_days in _AGING_RANGES:
                if days >= min_days and (max_days is None or days <= max_days):
                    buckets[label]["amount"] += outstanding
                    buckets[label]["count"] += 1
                    break

            total_pending += outstanding

        return AccountAgingSummary(
            buckets=[
                AccountAgingBucket(
                    label=label,
                    min_days=min_days,
                    max_days=max_days,
                    amount=buckets[label]["amount"],
                    invoice_count=buckets[label]["count"],
                )
                for label, min_days, max_days in _AGING_RANGES
            ],
            total_pending=total_pending,
        )

    def get_balance_history(
        self,
        supplier_id: int,
        limit: int = 60,
    ) -> list[AccountBalanceHistoryPoint]:
        supplier = self.supplier_repo.get_by_id(supplier_id)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proveedor no encontrado",
            )

        movements = self.repo.get_balance_history(supplier_id, limit=limit)
        return [
            AccountBalanceHistoryPoint(
                date=m.created_at,
                balance=m.balance_after,
                movement_type=m.movement_type,
                amount=m.amount,
            )
            for m in movements
        ]

    # ------------------------------------------------------------------
    # Enriquecimiento de respuesta (detalle de remito + asignaciones)
    # ------------------------------------------------------------------

    def _build_responses(
        self,
        movements: list[SupplierAccountMovement],
    ) -> list[SupplierAccountMovementResponse]:
        invoice_ids = {
            m.reference_id
            for m in movements
            if m.reference_type == "purchase_invoice" and m.reference_id is not None
        }

        invoices_by_id = {}
        if invoice_ids:
            invoices = self.purchase_invoice_repo.get_by_ids(list(invoice_ids))
            invoices_by_id = {inv.id: inv for inv in invoices}

        responses = []
        for movement in movements:
            base = SupplierAccountMovementResponse.model_validate(movement)

            reference_summary = None
            if movement.reference_type == "purchase_invoice" and movement.reference_id in invoices_by_id:
                reference_summary = InvoiceReferenceSummary.model_validate(
                    invoices_by_id[movement.reference_id]
                )

            allocations = [
                PaymentAllocationSummary(
                    invoice_id=a.purchase_invoice_id,
                    invoice_number=(
                        a.purchase_invoice.invoice_number if a.purchase_invoice else None
                    ),
                    amount_applied=a.amount_applied,
                )
                for a in (movement.allocations or [])
            ]

            responses.append(
                base.model_copy(
                    update={
                        "reference_summary": reference_summary,
                        "allocations": allocations,
                    }
                )
            )

        return responses
