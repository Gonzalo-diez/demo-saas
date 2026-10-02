from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.constants.checks_constant import ALLOWED_CHECK_STATUSES
from app.models.check_model import Check
from app.models.sales_rep_model import SalesRep
from app.repositories.check_repository import CheckRepository
from app.repositories.client_repository import ClientRepository
from app.repositories.purchase_invoice_repository import PurchaseInvoiceRepository
from app.repositories.purchase_quote_repository import PurchaseQuoteRepository
from app.repositories.sales_invoice_repository import SalesInvoiceRepository
from app.repositories.sales_quote_repository import SalesQuoteRepository
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.account_movement_schema import (
    ClientPaymentAllocationItem,
    ClientPaymentCreate,
    PaymentAllocationItem,
    SupplierPaymentCreate,
)
from app.schemas.check_schema import (
    CheckRejectRequest,
    IssuedCheckCreate,
    ReceivedCheckCreate,
)
from app.services.client_account_movement_service import ClientAccountMovementService
from app.services.notification_alert_service import NotificationAlertService
from app.services.supplier_account_movement_service import SupplierAccountMovementService

# document_type -> ("received"|"issued", repo attr en __init__)
_DOCUMENT_DIRECTION = {
    "sales_invoice": "received",
    "sales_quote": "received",
    "purchase_invoice": "issued",
    "purchase_quote": "issued",
}


class CheckService:
    """
    Cheques recibidos de clientes (cobro) y emitidos a proveedores (pago).

    El cheque se registra como 'pendiente' sin tocar ningún saldo. Recién
    al acreditarlo (`credit`) se genera el movimiento de cuenta corriente
    real, reusando ClientAccountMovementService/SupplierAccountMovementService
    tal cual como si el cobro/pago se hiciera en ese momento — mismas
    validaciones de imputación, mismo efecto sobre paid_amount/payment_status
    de los remitos/presupuestos.

    Si se rechaza, no hay nada que revertir: como el saldo nunca se tocó,
    la cuenta corriente queda como si el cheque no hubiese existido.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = CheckRepository(db)
        self.client_repo = ClientRepository(db)
        self.supplier_repo = SupplierRepository(db)
        self.sales_invoice_repo = SalesInvoiceRepository(db)
        self.sales_quote_repo = SalesQuoteRepository(db)
        self.purchase_invoice_repo = PurchaseInvoiceRepository(db)
        self.purchase_quote_repo = PurchaseQuoteRepository(db)
        self.client_movement_service = ClientAccountMovementService(db)
        self.supplier_movement_service = SupplierAccountMovementService(db)
        self.alert_service = NotificationAlertService(db)

    def _get_or_404(self, check_id: int, *, for_update: bool = False) -> Check:
        check = (
            self.repo.get_by_id_for_update(check_id)
            if for_update
            else self.repo.get_by_id(check_id)
        )
        if not check:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cheque no encontrado",
            )
        return check

    # ------------------------------------------------------------------
    # Alta
    # ------------------------------------------------------------------

    def register_received(
        self,
        client_id: int,
        data: ReceivedCheckCreate,
        current_user: Optional[SalesRep],
    ) -> Check:
        client = self.client_repo.get_by_id(client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado",
            )

        check = self.repo.create(
            direction="received",
            check_number=data.check_number,
            bank_name=data.bank_name,
            drawer_name=data.drawer_name,
            amount=data.amount,
            issue_date=data.issue_date,
            payment_date=data.payment_date,
            due_date=data.due_date,
            notes=data.notes,
            client_id=client_id,
            supplier_id=None,
            pending_allocations=(
                [a.model_dump(mode="json") for a in data.allocations]
                if data.allocations
                else None
            ),
            created_by=current_user.id if current_user else None,
        )
        self.alert_service.safe_sync_check(check)
        return check

    def register_issued(
        self,
        supplier_id: int,
        data: IssuedCheckCreate,
        current_user: Optional[SalesRep],
    ) -> Check:
        supplier = self.supplier_repo.get_by_id(supplier_id)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proveedor no encontrado",
            )

        check = self.repo.create(
            direction="issued",
            check_number=data.check_number,
            bank_name=data.bank_name,
            drawer_name=data.drawer_name,
            amount=data.amount,
            issue_date=data.issue_date,
            payment_date=data.payment_date,
            due_date=data.due_date,
            notes=data.notes,
            client_id=None,
            supplier_id=supplier_id,
            pending_allocations=(
                [a.model_dump(mode="json") for a in data.allocations]
                if data.allocations
                else None
            ),
            created_by=current_user.id if current_user else None,
        )
        self.alert_service.safe_sync_check(check)
        return check

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def mark_as_deposited(self, check_id: int) -> Check:
        check = self._get_or_404(check_id, for_update=True)

        if check.status != "pendiente":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El cheque está en estado '{check.status}', no se puede depositar",
            )

        check.status = "depositado"
        check.deposited_at = datetime.now(timezone.utc)
        self.db.add(check)
        self.db.flush()
        self.db.refresh(check)
        self.alert_service.safe_sync_check(check)
        return check

    def credit(self, check_id: int, current_user: Optional[SalesRep]) -> Check:
        """
        Acredita el cheque: recién acá se genera el movimiento de cuenta
        corriente (payment) y, si había imputaciones pendientes, se
        aplican sobre los remitos/presupuestos correspondientes.
        """
        check = self._get_or_404(check_id, for_update=True)

        if check.status not in ("pendiente", "depositado"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El cheque está en estado '{check.status}', no se puede acreditar",
            )

        notes = f"Cheque #{check.check_number} acreditado"
        if check.notes:
            notes += f" — {check.notes}"

        if check.direction == "received":
            allocations = (
                [ClientPaymentAllocationItem(**item) for item in check.pending_allocations]
                if check.pending_allocations
                else None
            )
            movement = self.client_movement_service._register_payment_internal(
                check.client_id,
                ClientPaymentCreate(
                    amount=check.amount,
                    payment_method="cheque",
                    notes=notes,
                    allocations=allocations,
                ),
                current_user,
            )
            check.client_account_movement_id = movement.id
        else:
            allocations = (
                [PaymentAllocationItem(**item) for item in check.pending_allocations]
                if check.pending_allocations
                else None
            )
            movement = self.supplier_movement_service._register_payment_internal(
                check.supplier_id,
                SupplierPaymentCreate(
                    amount=check.amount,
                    payment_method="cheque",
                    notes=notes,
                    allocations=allocations,
                ),
                current_user,
            )
            check.supplier_account_movement_id = movement.id

        check.status = "acreditado"
        check.resolved_at = datetime.now(timezone.utc)
        self.db.add(check)
        self.db.flush()
        self.db.refresh(check)
        self.alert_service.safe_sync_check(check)
        return check

    def reject(
        self,
        check_id: int,
        data: CheckRejectRequest,
    ) -> Check:
        """
        Rechaza el cheque (rebotó). Como nunca se tocó el saldo, no hay
        nada que revertir: la cuenta corriente sigue como si el cheque
        no hubiese existido.
        """
        check = self._get_or_404(check_id, for_update=True)

        if check.status not in ("pendiente", "depositado"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El cheque está en estado '{check.status}', no se puede rechazar",
            )

        check.status = "rechazado"
        check.resolved_at = datetime.now(timezone.utc)
        if data.notes:
            check.notes = f"{check.notes}\n{data.notes}" if check.notes else data.notes
        self.db.add(check)
        self.db.flush()
        self.db.refresh(check)
        self.alert_service.safe_notify_check_rejected(check)
        return check

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def get_by_id(self, check_id: int) -> Check:
        return self._get_or_404(check_id)

    def get_checks(
        self,
        page: int = 1,
        page_size: int = 20,
        direction: Optional[str] = None,
        status_value: Optional[str] = None,
        client_id: Optional[int] = None,
        supplier_id: Optional[int] = None,
        due_before=None,
    ) -> dict:
        if status_value and status_value not in ALLOWED_CHECK_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estado inválido. Los estados permitidos son: {', '.join(ALLOWED_CHECK_STATUSES)}"
            )
            
        checks, total = self.repo.get_checks(
            page=max(1, page),
            page_size=max(1, page_size),
            direction=direction,
            status_value=status_value,
            client_id=client_id,
            supplier_id=supplier_id,
            due_before=due_before,
        )

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return {
            "checks": checks,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_pending_summary_for_client(self, client_id: int) -> dict:
        """
        Total de cheques recibidos de este cliente que todavía no se
        acreditaron ni rechazaron (para mostrar en la ficha del cliente
        junto a su saldo de cuenta corriente).
        """
        checks = self.repo.get_active_by_client(client_id)
        pending_amount = sum((c.amount for c in checks), Decimal("0.00"))
        return {
            "pending_amount": pending_amount,
            "pending_count": len(checks),
            "checks": checks,
        }

    def get_pending_summary_for_supplier(self, supplier_id: int) -> dict:
        """Igual que get_pending_summary_for_client, para cheques emitidos
        a un proveedor."""
        checks = self.repo.get_active_by_supplier(supplier_id)
        pending_amount = sum((c.amount for c in checks), Decimal("0.00"))
        return {
            "pending_amount": pending_amount,
            "pending_count": len(checks),
            "checks": checks,
        }

    def get_pending_checks_for_document(
        self,
        document_type: str,
        invoice_id: int,
    ) -> dict:
        """
        Cheques activos (pendientes/depositados) que tienen imputada una
        parte de su monto a este remito/presupuesto puntual — para mostrar
        en la ficha del documento "tiene un cheque en cartera por $X".
        """
        direction = _DOCUMENT_DIRECTION.get(document_type)
        if direction is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="document_type inválido",
            )

        if document_type == "sales_invoice":
            document = self.sales_invoice_repo.get_by_id(invoice_id)
        elif document_type == "sales_quote":
            document = self.sales_quote_repo.get_by_id(invoice_id)
        elif document_type == "purchase_invoice":
            document = self.purchase_invoice_repo.get_by_id(invoice_id)
        else:
            document = self.purchase_quote_repo.get_by_id(invoice_id)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento {document_type} #{invoice_id} no encontrado",
            )

        if direction == "received":
            candidates = self.repo.get_active_by_client(document.client_id)
        else:
            candidates = self.repo.get_active_by_supplier(document.supplier_id)

        matching = []
        pending_amount = Decimal("0.00")

        for check in candidates:
            for allocation in (check.pending_allocations or []):
                if (
                    allocation.get("document_type") == document_type
                    and allocation.get("invoice_id") == invoice_id
                ):
                    matching.append(check)
                    pending_amount += Decimal(str(allocation.get("amount", 0)))
                    break

        return {"pending_amount": pending_amount, "checks": matching}