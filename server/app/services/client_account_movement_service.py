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
from app.models.client_account_movement_model import ClientAccountMovement
from app.models.client_model import Client
from app.models.client_payment_allocation_model import ClientPaymentAllocation
from app.models.sales_rep_model import SalesRep
from app.repositories.client_account_movement_repository import (
    ClientAccountMovementRepository,
)
from app.repositories.client_repository import ClientRepository
from app.repositories.sales_invoice_repository import SalesInvoiceRepository
from app.repositories.sales_quote_repository import SalesQuoteRepository
from app.services.sales_document_payment_rules import (
    ensure_sales_document_accepts_payments,
)
from app.schemas.account_movement_schema import (
    ClientAccountMovementResponse,
    ClientPaymentAllocationItem,
    ClientPaymentCreate,
    InvoiceReferenceSummary,
    PaymentAllocationSummary,
)
from app.schemas.account_movement_stats_schema import (
    AccountAgingBucket,
    AccountAgingSummary,
    AccountBalanceHistoryPoint,
    AccountBalanceSummary,
    AccountRankingItem,
)

# Rangos de antigüedad de deuda, en días desde la fecha del remito
_AGING_RANGES: list[tuple[str, int, int | None]] = [
    ("0-30 días", 0, 30),
    ("31-60 días", 31, 60),
    ("61-90 días", 61, 90),
    ("Más de 90 días", 91, None),
]

# Tipos que aumentan la deuda del cliente hacia nosotros
_INCREASING_TYPES = {"invoice"}
# Tipos que la reducen
_DECREASING_TYPES = {"invoice_reversal", "payment", "credit_note"}

class ClientAccountMovementService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ClientAccountMovementRepository(db)
        self.client_repo = ClientRepository(db)
        self.sales_invoice_repo = SalesInvoiceRepository(db)
        self.sales_quote_repo = SalesQuoteRepository(db)

    # ------------------------------------------------------------------
    # Movimientos
    # ------------------------------------------------------------------

    def apply_movement(
        self,
        *,
        client_id: int,
        movement_type: str,
        amount: Decimal,
        reference_type: str | None = None,
        reference_id: int | None = None,
        payment_method: str | None = None,
        notes: str | None = None,
        created_by: int | None = None,
    ) -> ClientAccountMovement:
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

        client = (
            self.db.query(Client)
            .filter(Client.id == client_id)
            .with_for_update()
            .first()
        )

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado",
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

        balance_before = Decimal(client.current_balance)
        balance_after = balance_before + signed_amount

        movement = self.repo.create_without_commit(
            {
                "client_id": client.id,
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

        client.current_balance = balance_after
        self.db.add(client)

        return movement

    def apply_manual_adjustment(
        self,
        *,
        client_id: int,
        delta_amount: Decimal,
        notes: str | None = None,
        created_by: int | None = None,
    ) -> ClientAccountMovement:
        if delta_amount == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El ajuste no puede ser 0",
            )

        client = (
            self.db.query(Client)
            .filter(Client.id == client_id)
            .with_for_update()
            .first()
        )

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado",
            )

        balance_before = Decimal(client.current_balance)
        balance_after = balance_before + delta_amount

        movement = self.repo.create_without_commit(
            {
                "client_id": client.id,
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

        client.current_balance = balance_after
        self.db.add(client)

        return movement

    # ------------------------------------------------------------------
    # Pagos con asignación opcional a remitos puntuales
    # ------------------------------------------------------------------

    def register_payment(
        self,
        client_id: int,
        data: ClientPaymentCreate,
        current_user: SalesRep | None,
    ) -> ClientAccountMovementResponse:
        if data.payment_method == "cheque":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Los cheques no se registran como pago inmediato: usá "
                    "POST /clients/{client_id}/checks. El cheque queda "
                    "'pendiente' y recién afecta el saldo cuando se marca "
                    "como acreditado."
                ),
            )

        return self._register_payment_internal(client_id, data, current_user)

    def _register_payment_internal(
        self,
        client_id: int,
        data: ClientPaymentCreate,
        current_user: SalesRep | None,
    ) -> ClientAccountMovementResponse:
        """
        Igual que register_payment pero sin el bloqueo de 'cheque': lo usa
        CheckService al acreditar un cheque recibido (ahí sí corresponde
        crear el movimiento con payment_method='cheque').
        """
        movement = self.apply_movement(
            client_id=client_id,
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
                client_id=client_id,
                allocations=data.allocations,
            )

        self.db.flush()
        self.db.refresh(movement)

        return self._build_responses([movement])[0]

    def _apply_payment_allocations(
        self,
        *,
        movement: ClientAccountMovement,
        client_id: int,
        allocations: list[ClientPaymentAllocationItem],
    ) -> None:
        """
        Imputa un cobro a uno o varios documentos de venta del cliente:
        remitos (document_type='sales_invoice') y/o presupuestos que nacieron
        de un pedido (document_type='sales_quote').
        """
        invoice_ids = [a.invoice_id for a in allocations if a.document_type == "sales_invoice"]
        quote_ids = [a.invoice_id for a in allocations if a.document_type == "sales_quote"]

        invoices_by_id = {
            inv.id: inv for inv in self.sales_invoice_repo.get_by_ids_for_update(invoice_ids)
        }
        quotes_by_id = {
            q.id: q for q in self.sales_quote_repo.get_by_ids_for_update(quote_ids)
        }

        for alloc in allocations:
            if alloc.document_type == "sales_quote":
                document = quotes_by_id.get(alloc.invoice_id)
                if not document:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Presupuesto de venta #{alloc.invoice_id} no encontrado",
                    )
                label = f"presupuesto #{document.quote_number}"
            else:
                document = invoices_by_id.get(alloc.invoice_id)
                if not document:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Remito de venta #{alloc.invoice_id} no encontrado",
                    )
                label = f"remito #{document.invoice_number}"

            # Regla compartida con el ledger: solo se cobra lo que generó deuda.
            ensure_sales_document_accepts_payments(alloc.document_type, document, label)

            if document.client_id != client_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El {label} no pertenece a este cliente",
                )

            total = document.total_amount or Decimal("0.00")
            remaining = total - document.paid_amount

            if alloc.amount > remaining:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"El monto asignado al {label} "
                        f"supera su saldo pendiente (${remaining})"
                    ),
                )

            document.paid_amount = document.paid_amount + alloc.amount

            if document.paid_amount >= total and total > 0:
                document.payment_status = "paid"
            elif document.paid_amount > 0:
                document.payment_status = "partial"
            else:
                document.payment_status = "pending"

            self.db.add(document)

            if alloc.document_type == "sales_quote":
                allocation_row = ClientPaymentAllocation(
                    client_account_movement_id=movement.id,
                    sales_quote_id=document.id,
                    amount_applied=alloc.amount,
                )
            else:
                allocation_row = ClientPaymentAllocation(
                    client_account_movement_id=movement.id,
                    sales_invoice_id=document.id,
                    amount_applied=alloc.amount,
                )
            self.db.add(allocation_row)

        self.db.flush()

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def get_by_id(self, movement_id: int) -> ClientAccountMovementResponse:
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
        client_id: int | None = None,
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

        if client_id is not None:
            client = self.client_repo.get_by_id(client_id)
            if not client:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cliente no encontrado",
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
            client_id=client_id,
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

    def get_client_movements(
        self,
        client_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        return self.get_movements(
            page=page,
            page_size=page_size,
            client_id=client_id,
        )

    # ------------------------------------------------------------------
    # Métricas
    # ------------------------------------------------------------------

    def get_balance_summary(self) -> AccountBalanceSummary:
        total_debt, total_favor, debtor_count, favor_count = (
            self.client_repo.get_balance_summary_row()
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

        clients = self.client_repo.get_top_by_balance(
            limit=limit,
            ascending=order == "favor",
        )
        return [
            AccountRankingItem(id=c.id, name=c.name, balance=c.current_balance)
            for c in clients
        ]

    def get_aging_summary(self) -> AccountAgingSummary:
        # Remitos y presupuestos-de-pedido con saldo pendiente: los dos son
        # deuda del cliente, solo cambia el nombre de la columna de fecha.
        documents = [
            (inv, inv.invoice_date) for inv in self.sales_invoice_repo.get_pending_for_aging()
        ] + [
            (q, q.quote_date) for q in self.sales_quote_repo.get_pending_for_aging()
        ]
        today = date.today()

        buckets = {
            label: {"amount": Decimal("0.00"), "count": 0}
            for label, _, _ in _AGING_RANGES
        }
        total_pending = Decimal("0.00")

        for invoice, document_date in documents:
            outstanding = (invoice.total_amount or Decimal("0.00")) - invoice.paid_amount
            if outstanding <= 0:
                continue

            days = (today - document_date).days
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
        client_id: int,
        limit: int = 60,
    ) -> list[AccountBalanceHistoryPoint]:
        client = self.client_repo.get_by_id(client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado",
            )

        movements = self.repo.get_balance_history(client_id, limit=limit)
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
        movements: list[ClientAccountMovement],
    ) -> list[ClientAccountMovementResponse]:
        invoice_ids = {
            m.reference_id
            for m in movements
            if m.reference_type == "sales_invoice" and m.reference_id is not None
        }
        quote_ids = {
            m.reference_id
            for m in movements
            if m.reference_type == "sales_quote" and m.reference_id is not None
        }

        invoices_by_id = {}
        if invoice_ids:
            invoices = self.sales_invoice_repo.get_by_ids(list(invoice_ids))
            invoices_by_id = {inv.id: inv for inv in invoices}

        quotes_by_id = {}
        if quote_ids:
            quotes = self.sales_quote_repo.get_by_ids(list(quote_ids))
            quotes_by_id = {q.id: q for q in quotes}

        responses = []
        for movement in movements:
            base = ClientAccountMovementResponse.model_validate(movement)

            reference_summary = None
            if movement.reference_type == "sales_invoice" and movement.reference_id in invoices_by_id:
                reference_summary = InvoiceReferenceSummary.model_validate(
                    invoices_by_id[movement.reference_id]
                )
            elif movement.reference_type == "sales_quote" and movement.reference_id in quotes_by_id:
                quote = quotes_by_id[movement.reference_id]
                reference_summary = InvoiceReferenceSummary(
                    id=quote.id,
                    invoice_number=quote.quote_number,
                    invoice_date=quote.quote_date,
                    total_amount=quote.total_amount,
                    payment_status=quote.payment_status,
                    document_type="sales_quote",
                )

            allocations = []
            for a in (movement.allocations or []):
                if a.sales_quote_id is not None:
                    allocations.append(
                        PaymentAllocationSummary(
                            invoice_id=a.sales_quote_id,
                            invoice_number=(
                                a.sales_quote.quote_number if a.sales_quote else None
                            ),
                            amount_applied=a.amount_applied,
                            document_type="sales_quote",
                        )
                    )
                else:
                    allocations.append(
                        PaymentAllocationSummary(
                            invoice_id=a.sales_invoice_id,
                            invoice_number=(
                                a.sales_invoice.invoice_number if a.sales_invoice else None
                            ),
                            amount_applied=a.amount_applied,
                            document_type="sales_invoice",
                        )
                    )

            responses.append(
                base.model_copy(
                    update={
                        "reference_summary": reference_summary,
                        "allocations": allocations,
                    }
                )
            )

        return responses
