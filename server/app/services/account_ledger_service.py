from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.constants.account_movement_constant import ALLOWED_PAYMENT_METHODS
from app.models.client_account_movement_model import ClientAccountMovement
from app.models.client_payment_allocation_model import ClientPaymentAllocation
from app.models.purchase_invoice_model import PurchaseInvoice
from app.models.purchase_quote_model import PurchaseQuote
from app.models.sales_invoice_model import SalesInvoice
from app.models.sales_quote_model import SalesQuote
from app.models.sales_rep_model import SalesRep
from app.models.supplier_account_movement_model import SupplierAccountMovement
from app.models.supplier_payment_allocation_model import SupplierPaymentAllocation
from app.repositories.account_ledger_repository import AccountLedgerRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.sales_rep_repository import SalesRepRepository
from app.services.sales_document_payment_rules import (
    ensure_purchase_document_accepts_payments,
    ensure_sales_document_accepts_payments,
)
from app.schemas.account_ledger_schema import (
    ClientSaleRow,
    ClientSalesLedgerResponse,
    ClientSalesSummaryGroup,
    ClientSalesSummaryResponse,
    LedgerPaymentEntry,
    LedgerProductLine,
    SalesRepSummary,
    SupplierPurchaseRow,
    SupplierPurchasesGroup,
    SupplierPurchasesLedgerResponse,
)

ZERO = Decimal("0.00")


def _payment_status_for(paid_amount: Decimal, total_amount: Decimal | None) -> str:
    total = total_amount or ZERO
    if total > 0 and paid_amount >= total:
        return "paid"
    if paid_amount > 0:
        return "partial"
    return "pending"


class AccountLedgerService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AccountLedgerRepository(db)
        self.sales_rep_repo = SalesRepRepository(db)
        self.product_repo = ProductRepository(db)

    # ==================================================================
    # Proveedores (Compras)
    # ==================================================================

    def get_supplier_purchases_ledger(
        self,
        sales_rep_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> SupplierPurchasesLedgerResponse:
        purchases = self.repo.get_purchases(
            sales_rep_id=sales_rep_id,
            date_from=date_from,
            date_to=date_to,
        )

        groups_map: dict[int | None, SupplierPurchasesGroup] = {}

        if sales_rep_id is None:
            active_reps, _ = self.sales_rep_repo.get_sales_reps(
                page=1, page_size=1000, status="active", sort="name"
            )
            for rep in active_reps:
                groups_map[rep.id] = SupplierPurchasesGroup(
                    sales_rep=SalesRepSummary(id=rep.id, name=rep.name),
                    rows=[],
                    total=0,
                )

        for doc_type, doc in purchases:
            rep_key = doc.created_by
            if rep_key not in groups_map:
                rep_summary = (
                    SalesRepSummary(id=doc.creator.id, name=doc.creator.name)
                    if getattr(doc, "creator", None)
                    else None
                )
                groups_map[rep_key] = SupplierPurchasesGroup(
                    sales_rep=rep_summary, rows=[], total=0
                )

            groups_map[rep_key].rows.append(self._build_supplier_row(doc_type, doc))

        for group in groups_map.values():
            group.total = len(group.rows)

        groups = sorted(
            groups_map.values(),
            key=lambda g: (g.sales_rep is None, g.sales_rep.name if g.sales_rep else ""),
        )

        return SupplierPurchasesLedgerResponse(groups=groups)

    def add_supplier_payment(
        self,
        document_type: Literal["purchase_invoice", "purchase_quote"],
        document_id: int,
        amount: Decimal,
        method: str,
        payment_date: datetime | None,
        notes: str | None,
        current_user: SalesRep | None,
    ) -> SupplierPurchaseRow:
        self._validate_payment_method(method)

        if document_type == "purchase_quote":
            doc = self.repo.get_purchase_quote_for_update(document_id)
            alloc_kwargs = {"purchase_quote_id": document_id}
        else:
            doc = self.repo.get_purchase_invoice_for_update(document_id)
            alloc_kwargs = {"purchase_invoice_id": document_id}

        if not doc or doc.supplier_id is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Documento de compra no encontrado")

        ensure_purchase_document_accepts_payments(
            document_type,
            f"presupuesto #{doc.quote_number}"
            if document_type == "purchase_quote"
            else f"remito #{doc.invoice_number}",
        )

        total = doc.total_amount or ZERO
        remaining = total - doc.paid_amount
        if amount > remaining:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"El monto supera la deuda pendiente del documento (${remaining})",
            )

        supplier = self.repo.get_supplier_for_update(doc.supplier_id)
        if not supplier:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Proveedor no encontrado")

        balance_before = Decimal(supplier.current_balance)
        signed_amount = -amount
        balance_after = balance_before + signed_amount

        movement = SupplierAccountMovement(
            supplier_id=supplier.id,
            movement_type="payment",
            amount=signed_amount,
            balance_before=balance_before,
            balance_after=balance_after,
            reference_type="payment",
            payment_method=method,
            notes=notes,
            created_by=current_user.id if current_user else None,
        )
        if payment_date:
            movement.created_at = payment_date
        self.db.add(movement)
        self.db.flush()

        allocation = SupplierPaymentAllocation(
            supplier_account_movement_id=movement.id,
            amount_applied=amount,
            **alloc_kwargs,
        )
        self.db.add(allocation)

        doc.paid_amount += amount
        doc.payment_status = _payment_status_for(doc.paid_amount, total)
        supplier.current_balance = balance_after

        self.db.add(doc)
        self.db.add(supplier)
        self.db.flush()
        self.db.refresh(doc)

        return self._build_supplier_row(document_type, doc)

    def edit_supplier_payment(
        self,
        allocation_id: int,
        amount: Decimal | None,
        method: str | None,
        payment_date: datetime | None,
        notes: str | None,
    ) -> SupplierPurchaseRow:
        allocation = self.repo.get_supplier_payment_allocation_for_update(allocation_id)
        if not allocation:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Pago no encontrado")

        movement = allocation.movement
        doc = allocation.purchase_invoice or allocation.purchase_quote
        doc_type: Literal["purchase_invoice", "purchase_quote"] = (
            "purchase_invoice" if allocation.purchase_invoice_id else "purchase_quote"
        )

        self._ensure_single_allocation_movement(movement, "proveedor")

        if method is not None:
            self._validate_payment_method(method)

        supplier = self.repo.get_supplier_for_update(doc.supplier_id)
        if not supplier:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Proveedor no encontrado")

        new_amount = amount if amount is not None else allocation.amount_applied
        total = doc.total_amount or ZERO
        remaining = total - doc.paid_amount + allocation.amount_applied
        if new_amount > remaining:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"El monto supera la deuda pendiente del documento (${remaining})",
            )

        doc.paid_amount = doc.paid_amount - allocation.amount_applied + new_amount
        doc.payment_status = _payment_status_for(doc.paid_amount, total)
        allocation.amount_applied = new_amount

        old_signed = Decimal(movement.amount)
        new_signed = -new_amount
        delta = new_signed - old_signed
        movement.amount = new_signed
        movement.balance_after = movement.balance_before + new_signed
        if method is not None:
            movement.payment_method = method
        if notes is not None:
            movement.notes = notes
        if payment_date is not None:
            movement.created_at = payment_date

        self.repo.shift_balance_chain(
            SupplierAccountMovement, "supplier_id", supplier.id, movement.id, delta
        )
        supplier.current_balance = Decimal(supplier.current_balance) + delta

        self.db.add_all([movement, allocation, doc, supplier])
        self.db.flush()
        self.db.refresh(doc)

        return self._build_supplier_row(doc_type, doc)

    def delete_supplier_payment(self, allocation_id: int) -> SupplierPurchaseRow:
        allocation = self.repo.get_supplier_payment_allocation_for_update(allocation_id)
        if not allocation:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Pago no encontrado")

        movement = allocation.movement
        doc = allocation.purchase_invoice or allocation.purchase_quote
        doc_type: Literal["purchase_invoice", "purchase_quote"] = (
            "purchase_invoice" if allocation.purchase_invoice_id else "purchase_quote"
        )

        self._ensure_single_allocation_movement(movement, "proveedor")

        supplier = self.repo.get_supplier_for_update(doc.supplier_id)
        if not supplier:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Proveedor no encontrado")

        total = doc.total_amount or ZERO
        doc.paid_amount -= allocation.amount_applied
        doc.payment_status = _payment_status_for(doc.paid_amount, total)

        delta = -Decimal(movement.amount)
        self.repo.shift_balance_chain(
            SupplierAccountMovement, "supplier_id", supplier.id, movement.id, delta
        )
        supplier.current_balance = Decimal(supplier.current_balance) + delta

        self.db.delete(allocation)
        self.db.delete(movement)
        self.db.add_all([doc, supplier])
        self.db.flush()
        self.db.refresh(doc)

        return self._build_supplier_row(doc_type, doc)

    # ==================================================================
    # Clientes (Ventas)
    # ==================================================================

    def get_client_sales_ledger(
        self,
        page: int = 1,
        page_size: int = 20,
        client_id: int | None = None,
        sales_rep_id: int | None = None,
        only_unassigned: bool = False,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> ClientSalesLedgerResponse:
        sales_items, total = self.repo.get_client_sales(
            page=page,
            page_size=page_size,
            client_id=client_id,
            sales_rep_id=sales_rep_id,
            only_unassigned=only_unassigned,
            date_from=date_from,
            date_to=date_to,
        )

        stock_by_product = self._get_stock_map(sales_items)
        rows = [
            self._build_client_row(doc_type, doc, stock_by_product)
            for doc_type, doc in sales_items
        ]

        total_pages = max(1, (total + page_size - 1) // page_size) if page_size else 1
        return ClientSalesLedgerResponse(
            items=rows, total=total, page=page, page_size=page_size, total_pages=total_pages
        )

    def get_client_sales_summary(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> ClientSalesSummaryResponse:
        counts = self.repo.get_client_sales_counts_by_rep(date_from=date_from, date_to=date_to)
        counts_by_rep_id: dict[int, int] = {}
        unassigned_count = 0
        names_by_rep_id: dict[int, str] = {}
        for rep_id, name, count in counts:
            if rep_id is None:
                unassigned_count += count
            else:
                counts_by_rep_id[rep_id] = count
                if name:
                    names_by_rep_id[rep_id] = name

        active_reps, _ = self.sales_rep_repo.get_sales_reps(
            page=1, page_size=1000, status="active", sort="name"
        )

        groups: list[ClientSalesSummaryGroup] = []
        seen_ids: set[int] = set()
        for rep in active_reps:
            groups.append(
                ClientSalesSummaryGroup(
                    sales_rep=SalesRepSummary(id=rep.id, name=rep.name),
                    total=counts_by_rep_id.get(rep.id, 0),
                )
            )
            seen_ids.add(rep.id)

        for rep_id, count in counts_by_rep_id.items():
            if rep_id not in seen_ids:
                groups.append(
                    ClientSalesSummaryGroup(
                        sales_rep=SalesRepSummary(
                            id=rep_id, name=names_by_rep_id.get(rep_id, f"Vendedor #{rep_id}")
                        ),
                        total=count,
                    )
                )
                seen_ids.add(rep_id)

        if unassigned_count > 0:
            groups.append(ClientSalesSummaryGroup(sales_rep=None, total=unassigned_count))

        groups.sort(key=lambda g: (g.sales_rep is None, g.sales_rep.name if g.sales_rep else ""))
        total_all = sum(g.total for g in groups)

        return ClientSalesSummaryResponse(groups=groups, total_all=total_all)

    def add_client_payment(
        self,
        document_type: Literal["sales_invoice", "sales_quote"],
        document_id: int,
        amount: Decimal,
        method: str,
        payment_date: datetime | None,
        notes: str | None,
        current_user: SalesRep | None,
    ) -> ClientSaleRow:
        self._validate_payment_method(method)

        if document_type == "sales_quote":
            doc = self.repo.get_sales_quote_for_update(document_id)
            alloc_kwargs = {"sales_quote_id": document_id}
        else:
            doc = self.repo.get_sales_invoice_for_update(document_id)
            alloc_kwargs = {"sales_invoice_id": document_id}

        if not doc or doc.client_id is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Venta a cliente no encontrada")

        doc_number = doc.quote_number if document_type == "sales_quote" else doc.invoice_number
        label = (
            f"presupuesto #{doc_number}"
            if document_type == "sales_quote"
            else f"remito #{doc_number}"
        )
        # Misma regla que ClientAccountMovementService: no se cobran cotizaciones
        # sueltas ni documentos que no generaron (o ya revirtieron) deuda.
        ensure_sales_document_accepts_payments(document_type, doc, label)

        total = doc.total_amount or ZERO
        remaining = total - doc.paid_amount
        if amount > remaining:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"El monto supera la deuda pendiente del documento (${remaining})",
            )

        client = self.repo.get_client_for_update(doc.client_id)
        if not client:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado")

        balance_before = Decimal(client.current_balance)
        signed_amount = -amount
        balance_after = balance_before + signed_amount

        movement = ClientAccountMovement(
            client_id=client.id,
            movement_type="payment",
            amount=signed_amount,
            balance_before=balance_before,
            balance_after=balance_after,
            reference_type="payment",
            payment_method=method,
            notes=notes,
            created_by=current_user.id if current_user else None,
        )
        if payment_date:
            movement.created_at = payment_date
        self.db.add(movement)
        self.db.flush()

        allocation = ClientPaymentAllocation(
            client_account_movement_id=movement.id,
            amount_applied=amount,
            **alloc_kwargs,
        )
        self.db.add(allocation)

        doc.paid_amount += amount
        doc.payment_status = _payment_status_for(doc.paid_amount, total)
        client.current_balance = balance_after

        self.db.add(doc)
        self.db.add(client)
        self.db.flush()
        self.db.refresh(doc)

        return self._build_client_row(
            document_type, doc, self._get_stock_map([(document_type, doc)])
        )

    def edit_client_payment(
        self,
        allocation_id: int,
        amount: Decimal | None,
        method: str | None,
        payment_date: datetime | None,
        notes: str | None,
    ) -> ClientSaleRow:
        allocation = self.repo.get_client_payment_allocation_for_update(allocation_id)
        if not allocation:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Pago no encontrado")

        movement = allocation.movement
        doc = allocation.sales_invoice or allocation.sales_quote
        doc_type: Literal["sales_invoice", "sales_quote"] = (
            "sales_invoice" if allocation.sales_invoice_id else "sales_quote"
        )

        self._ensure_single_allocation_movement(movement, "cliente")

        if method is not None:
            self._validate_payment_method(method)

        client = self.repo.get_client_for_update(doc.client_id)
        if not client:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado")

        new_amount = amount if amount is not None else allocation.amount_applied
        total = doc.total_amount or ZERO
        remaining = total - doc.paid_amount + allocation.amount_applied
        if new_amount > remaining:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"El monto supera la deuda pendiente del documento (${remaining})",
            )

        doc.paid_amount = doc.paid_amount - allocation.amount_applied + new_amount
        doc.payment_status = _payment_status_for(doc.paid_amount, total)
        allocation.amount_applied = new_amount

        old_signed = Decimal(movement.amount)
        new_signed = -new_amount
        delta = new_signed - old_signed
        movement.amount = new_signed
        movement.balance_after = movement.balance_before + new_signed
        if method is not None:
            movement.payment_method = method
        if notes is not None:
            movement.notes = notes
        if payment_date is not None:
            movement.created_at = payment_date

        self.repo.shift_balance_chain(
            ClientAccountMovement, "client_id", client.id, movement.id, delta
        )
        client.current_balance = Decimal(client.current_balance) + delta

        self.db.add_all([movement, allocation, doc, client])
        self.db.flush()
        self.db.refresh(doc)

        return self._build_client_row(
            doc_type, doc, self._get_stock_map([(doc_type, doc)])
        )

    def delete_client_payment(self, allocation_id: int) -> ClientSaleRow:
        allocation = self.repo.get_client_payment_allocation_for_update(allocation_id)
        if not allocation:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Pago no encontrado")

        movement = allocation.movement
        doc = allocation.sales_invoice or allocation.sales_quote
        doc_type: Literal["sales_invoice", "sales_quote"] = (
            "sales_invoice" if allocation.sales_invoice_id else "sales_quote"
        )

        self._ensure_single_allocation_movement(movement, "cliente")

        client = self.repo.get_client_for_update(doc.client_id)
        if not client:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado")

        total = doc.total_amount or ZERO
        doc.paid_amount -= allocation.amount_applied
        doc.payment_status = _payment_status_for(doc.paid_amount, total)

        delta = -Decimal(movement.amount)
        self.repo.shift_balance_chain(
            ClientAccountMovement, "client_id", client.id, movement.id, delta
        )
        client.current_balance = Decimal(client.current_balance) + delta

        self.db.delete(allocation)
        self.db.delete(movement)
        self.db.add_all([doc, client])
        self.db.flush()
        self.db.refresh(doc)

        return self._build_client_row(
            doc_type, doc, self._get_stock_map([(doc_type, doc)])
        )

    # ==================================================================
    # Helpers
    # ==================================================================

    def _validate_payment_method(self, method: str) -> None:
        if method not in ALLOWED_PAYMENT_METHODS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Método de pago inválido")

    def _ensure_single_allocation_movement(self, movement, entity_label: str) -> None:
        if movement is None or len(movement.allocations or []) != 1:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                (
                    f"Este pago está repartido entre varios comprobantes de {entity_label}; "
                    "no se puede editar ni borrar desde esta pantalla."
                ),
            )

    def _get_stock_map(
        self, items: list[tuple[str, SalesInvoice | SalesQuote]]
    ) -> dict[int, int]:
        product_ids = {
            item.product_id
            for _, doc in items
            for item in doc.items
            if item.product_id
        }
        if not product_ids:
            return {}

        products = self.product_repo.get_products_by_ids(list(product_ids))
        return {p.id: p.stock_current for p in products}

    def _build_supplier_row(
        self,
        doc_type: Literal["purchase_invoice", "purchase_quote"],
        doc: PurchaseInvoice | PurchaseQuote,
    ) -> SupplierPurchaseRow:
        products = [
            LedgerProductLine(
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
            )
            for item in doc.items
        ]
        payments = [
            LedgerPaymentEntry(
                id=alloc.id,
                method=alloc.movement.payment_method or "otro",
                amount=alloc.amount_applied,
                date=alloc.movement.created_at,
            )
            for alloc in doc.payment_allocations
        ]

        doc_date = getattr(doc, "invoice_date", getattr(doc, "quote_date", None))
        doc_number = getattr(doc, "invoice_number", getattr(doc, "quote_number", None))

        return SupplierPurchaseRow(
            id=doc.id,
            document_type=doc_type,
            document_number=str(doc_number) if doc_number else None,
            purchase_date=doc_date,
            supplier_id=doc.supplier_id,
            supplier_name=getattr(
                doc,
                "supplier_name",
                doc.supplier.name if doc.supplier else "Proveedor",
            ),
            products=products,
            total_quantity=sum(p.quantity for p in products),
            total_amount=doc.total_amount,
            payments=payments,
            paid_amount=doc.paid_amount,
            balance=(doc.total_amount or ZERO) - doc.paid_amount,
            payment_status=doc.payment_status,
        )

    def _build_client_row(
        self,
        doc_type: Literal["sales_invoice", "sales_quote"],
        doc: SalesInvoice | SalesQuote,
        stock_by_product: dict[int, int],
    ) -> ClientSaleRow:
        products = [
            LedgerProductLine(
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                stock_current=stock_by_product.get(item.product_id),
            )
            for item in doc.items
        ]
        payments = [
            LedgerPaymentEntry(
                id=alloc.id,
                method=alloc.movement.payment_method or "otro",
                amount=alloc.amount_applied,
                date=alloc.movement.created_at,
            )
            for alloc in doc.payment_allocations
        ]

        raw_sales_type = getattr(doc, "sales_type", None)
        if hasattr(raw_sales_type, "value"):
            sales_type_str = raw_sales_type.value
        elif raw_sales_type:
            sales_type_str = str(raw_sales_type)
        else:
            sales_type_str = "B2B"

        doc_date = getattr(doc, "invoice_date", getattr(doc, "quote_date", None))
        doc_number = getattr(doc, "invoice_number", getattr(doc, "quote_number", None))

        return ClientSaleRow(
            id=doc.id,
            document_type=doc_type,
            document_number=str(doc_number) if doc_number else None,
            sale_date=doc_date,
            client_id=doc.client_id,
            client_name=doc.client.name
            if doc.client
            else (getattr(doc, "customer_name", None) or "Cliente"),
            sales_type=sales_type_str,
            products=products,
            total_quantity=sum(p.quantity for p in products),
            total_amount=doc.total_amount,
            payments=payments,
            paid_amount=doc.paid_amount,
            balance=(doc.total_amount or ZERO) - doc.paid_amount,
            payment_status=doc.payment_status,
        )