from datetime import date
from typing import List, Literal, Optional, Tuple, Type
from sqlalchemy import func, literal_column, select, union_all
from sqlalchemy.orm import Session, joinedload, selectinload
from app.models.client_model import Client
from app.models.client_payment_allocation_model import ClientPaymentAllocation
from app.models.purchase_invoice_model import PurchaseInvoice
from app.models.purchase_quote_model import PurchaseQuote
from app.models.sales_invoice_model import SalesInvoice
from app.models.sales_quote_model import SalesQuote
from app.models.sales_rep_model import SalesRep
from app.models.supplier_model import Supplier
from app.models.supplier_payment_allocation_model import SupplierPaymentAllocation


class AccountLedgerRepository:
    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # 1. PROVEEDORES (COMPRAS: PurchaseInvoice + PurchaseQuote)
    # =========================================================================

    def get_purchases(
        self,
        sales_rep_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Tuple[Literal["purchase_invoice", "purchase_quote"], PurchaseInvoice | PurchaseQuote]]:
        """
        Trae todas las facturas y presupuestos de compra (con ítems, proveedor,
        vendedor creador y pagos aplicados) para el ledger de Proveedores.
        Sin paginación (se agrupa por sales_rep en el service).
        """
        # --- 1. Facturas / Remitos de Compra ---
        q_inv = (
            select(PurchaseInvoice)
            .options(
                selectinload(PurchaseInvoice.items),
                joinedload(PurchaseInvoice.creator),
                joinedload(PurchaseInvoice.supplier),
                selectinload(PurchaseInvoice.payment_allocations).joinedload(
                    SupplierPaymentAllocation.movement
                ),
            )
        )
        if sales_rep_id:
            q_inv = q_inv.where(PurchaseInvoice.created_by == sales_rep_id)
        if date_from:
            q_inv = q_inv.where(PurchaseInvoice.invoice_date >= date_from)
        if date_to:
            q_inv = q_inv.where(PurchaseInvoice.invoice_date <= date_to)

        invoices = self.db.scalars(q_inv).unique().all()

        # --- 2. Presupuestos de Compra ---
        q_quote = (
            select(PurchaseQuote)
            .options(
                selectinload(PurchaseQuote.items),
                joinedload(PurchaseQuote.creator),
                joinedload(PurchaseQuote.supplier),
                selectinload(PurchaseQuote.payment_allocations).joinedload(
                    SupplierPaymentAllocation.movement
                ),
            )
        )
        if sales_rep_id:
            q_quote = q_quote.where(PurchaseQuote.created_by == sales_rep_id)
        if date_from:
            q_quote = q_quote.where(PurchaseQuote.quote_date >= date_from)
        if date_to:
            q_quote = q_quote.where(PurchaseQuote.quote_date <= date_to)

        quotes = self.db.scalars(q_quote).unique().all()

        # --- 3. Combinar y ordenar en memoria por fecha e ID desc ---
        combined: List[Tuple[Literal["purchase_invoice", "purchase_quote"], PurchaseInvoice | PurchaseQuote]] = []
        for inv in invoices:
            combined.append(("purchase_invoice", inv))
        for quote in quotes:
            combined.append(("purchase_quote", quote))

        def _get_sort_key(item):
            doc_type, doc = item
            doc_date = doc.invoice_date if doc_type == "purchase_invoice" else doc.quote_date
            return (doc_date, doc.id)

        combined.sort(key=_get_sort_key, reverse=True)
        return combined

    # =========================================================================
    # 2. CLIENTES (VENTAS: SalesInvoice + SalesQuote con UNION ALL Paginado)
    # =========================================================================

    def get_client_sales(
        self,
        page: int = 1,
        page_size: int = 20,
        client_id: Optional[int] = None,
        sales_rep_id: Optional[int] = None,
        only_unassigned: bool = False,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Tuple[List[Tuple[Literal["sales_invoice", "sales_quote"], SalesInvoice | SalesQuote]], int]:
        """
        Obtiene ventas (Remitos/Facturas y Presupuestos) en un listado unificado,
        ordenado por fecha descendente y paginado mediante UNION ALL en Base de Datos.
        """
        # -------------------------------------------------------------
        # Paso A: Definir subconsultas ligeras (solo IDs, tipos y fechas)
        # -------------------------------------------------------------
        sub_inv = select(
            SalesInvoice.id.label("doc_id"),
            literal_column("'sales_invoice'").label("doc_type"),
            SalesInvoice.invoice_date.label("doc_date"),
        )
        if client_id:
            sub_inv = sub_inv.where(SalesInvoice.client_id == client_id)
        if only_unassigned:
            sub_inv = sub_inv.where(SalesInvoice.sales_rep_id.is_(None))
        elif sales_rep_id:
            sub_inv = sub_inv.where(SalesInvoice.sales_rep_id == sales_rep_id)
        if date_from:
            sub_inv = sub_inv.where(SalesInvoice.invoice_date >= date_from)
        if date_to:
            sub_inv = sub_inv.where(SalesInvoice.invoice_date <= date_to)

        sub_quote = select(
            SalesQuote.id.label("doc_id"),
            literal_column("'sales_quote'").label("doc_type"),
            SalesQuote.quote_date.label("doc_date"),
        )
        if client_id:
            sub_quote = sub_quote.where(SalesQuote.client_id == client_id)
        if only_unassigned:
            sub_quote = sub_quote.where(SalesQuote.sales_rep_id.is_(None))
        elif sales_rep_id:
            sub_quote = sub_quote.where(SalesQuote.sales_rep_id == sales_rep_id)
        if date_from:
            sub_quote = sub_quote.where(SalesQuote.quote_date >= date_from)
        if date_to:
            sub_quote = sub_quote.where(SalesQuote.quote_date <= date_to)

        # -------------------------------------------------------------
        # Paso B: UNION ALL y Paginación
        # -------------------------------------------------------------
        combined_union = union_all(sub_inv, sub_quote).subquery()

        # Conteo total para meta de paginación
        count_stmt = select(func.count()).select_from(combined_union)
        total = self.db.scalar(count_stmt) or 0

        # Obtener las claves (ID + Tipo) correspondientes a la página actual
        paginated_stmt = (
            select(combined_union.c.doc_id, combined_union.c.doc_type)
            .order_by(combined_union.c.doc_date.desc(), combined_union.c.doc_id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        page_refs = self.db.execute(paginated_stmt).all()

        if not page_refs:
            return [], total

        # -------------------------------------------------------------
        # Paso C: Cargar las entidades ORM completas mediante IDs
        # -------------------------------------------------------------
        invoice_ids = [r.doc_id for r in page_refs if r.doc_type == "sales_invoice"]
        quote_ids = [r.doc_id for r in page_refs if r.doc_type == "sales_quote"]

        invoices_by_id = {}
        if invoice_ids:
            inv_stmt = (
                select(SalesInvoice)
                .options(
                    selectinload(SalesInvoice.items),
                    joinedload(SalesInvoice.client),
                    selectinload(SalesInvoice.payment_allocations).joinedload(
                        ClientPaymentAllocation.movement
                    ),
                )
                .where(SalesInvoice.id.in_(invoice_ids))
            )
            invoices = self.db.scalars(inv_stmt).unique().all()
            invoices_by_id = {inv.id: inv for inv in invoices}

        quotes_by_id = {}
        if quote_ids:
            quote_stmt = (
                select(SalesQuote)
                .options(
                    selectinload(SalesQuote.items),
                    joinedload(SalesQuote.client),
                    selectinload(SalesQuote.payment_allocations).joinedload(
                        ClientPaymentAllocation.movement
                    ),
                )
                .where(SalesQuote.id.in_(quote_ids))
            )
            quotes = self.db.scalars(quote_stmt).unique().all()
            quotes_by_id = {q.id: q for q in quotes}

        # -------------------------------------------------------------
        # Paso D: Reconstruir la lista respetando el orden exacto de la página
        # -------------------------------------------------------------
        results: List[Tuple[Literal["sales_invoice", "sales_quote"], SalesInvoice | SalesQuote]] = []
        for ref in page_refs:
            if ref.doc_type == "sales_invoice" and ref.doc_id in invoices_by_id:
                results.append(("sales_invoice", invoices_by_id[ref.doc_id]))
            elif ref.doc_type == "sales_quote" and ref.doc_id in quotes_by_id:
                results.append(("sales_quote", quotes_by_id[ref.doc_id]))

        return results, total

    def get_client_sales_counts_by_rep(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> list[tuple[Optional[int], Optional[str], int]]:
        """
        Suma los contadores de ventas (Remitos + Presupuestos) agrupados por
        vendedor para las pestañas/sub-pestañas.
        """
        # Conteo Invoices
        q_inv = (
            select(
                SalesInvoice.sales_rep_id,
                SalesRep.name,
                func.count(SalesInvoice.id).label("cnt"),
            )
            .outerjoin(SalesRep, SalesRep.id == SalesInvoice.sales_rep_id)
            .group_by(SalesInvoice.sales_rep_id, SalesRep.name)
        )
        if date_from:
            q_inv = q_inv.where(SalesInvoice.invoice_date >= date_from)
        if date_to:
            q_inv = q_inv.where(SalesInvoice.invoice_date <= date_to)

        # Conteo Quotes
        q_quote = (
            select(
                SalesQuote.sales_rep_id,
                SalesRep.name,
                func.count(SalesQuote.id).label("cnt"),
            )
            .outerjoin(SalesRep, SalesRep.id == SalesQuote.sales_rep_id)
            .group_by(SalesQuote.sales_rep_id, SalesRep.name)
        )
        if date_from:
            q_quote = q_quote.where(SalesQuote.quote_date >= date_from)
        if date_to:
            q_quote = q_quote.where(SalesQuote.quote_date <= date_to)

        inv_rows = self.db.execute(q_inv).all()
        quote_rows = self.db.execute(q_quote).all()

        # Consolidar en un diccionario por sales_rep_id
        rep_map = {}
        for rep_id, name, cnt in inv_rows:
            rep_map[rep_id] = {"name": name, "cnt": cnt}

        for rep_id, name, cnt in quote_rows:
            if rep_id in rep_map:
                rep_map[rep_id]["cnt"] += cnt
            else:
                rep_map[rep_id] = {"name": name, "cnt": cnt}

        return [(rep_id, data["name"], data["cnt"]) for rep_id, data in rep_map.items()]

    # =========================================================================
    # 3. GETTERS "FOR UPDATE" Y HELPERS DE PAGO
    # =========================================================================

    def get_purchase_invoice_for_update(self, purchase_invoice_id: int) -> Optional[PurchaseInvoice]:
        query = (
            select(PurchaseInvoice)
            .options(
                selectinload(PurchaseInvoice.items),
                selectinload(PurchaseInvoice.creator),
                selectinload(PurchaseInvoice.supplier),
                selectinload(PurchaseInvoice.payment_allocations).joinedload(
                    SupplierPaymentAllocation.movement
                ),
            )
            .where(PurchaseInvoice.id == purchase_invoice_id)
            .with_for_update(of=PurchaseInvoice)
        )
        return self.db.scalar(query)

    def get_purchase_quote_for_update(self, purchase_quote_id: int) -> Optional[PurchaseQuote]:
        query = (
            select(PurchaseQuote)
            .options(
                selectinload(PurchaseQuote.items),
                selectinload(PurchaseQuote.creator),
                selectinload(PurchaseQuote.supplier),
                selectinload(PurchaseQuote.payment_allocations).joinedload(
                    SupplierPaymentAllocation.movement
                ),
            )
            .where(PurchaseQuote.id == purchase_quote_id)
            .with_for_update(of=PurchaseQuote)
        )
        return self.db.scalar(query)

    def get_sales_invoice_for_update(self, sales_invoice_id: int) -> Optional[SalesInvoice]:
        query = (
            select(SalesInvoice)
            .options(
                selectinload(SalesInvoice.items),
                selectinload(SalesInvoice.client),
                selectinload(SalesInvoice.payment_allocations).joinedload(
                    ClientPaymentAllocation.movement
                ),
            )
            .where(SalesInvoice.id == sales_invoice_id)
            .with_for_update(of=SalesInvoice)
        )
        return self.db.scalar(query)

    def get_sales_quote_for_update(self, sales_quote_id: int) -> Optional[SalesQuote]:
        query = (
            select(SalesQuote)
            .options(
                selectinload(SalesQuote.items),
                selectinload(SalesQuote.client),
                selectinload(SalesQuote.payment_allocations).joinedload(
                    ClientPaymentAllocation.movement
                ),
            )
            .where(SalesQuote.id == sales_quote_id)
            .with_for_update(of=SalesQuote)
        )
        return self.db.scalar(query)

    def get_supplier_for_update(self, supplier_id: int) -> Optional[Supplier]:
        query = select(Supplier).where(Supplier.id == supplier_id).with_for_update()
        return self.db.scalar(query)

    def get_client_for_update(self, client_id: int) -> Optional[Client]:
        query = select(Client).where(Client.id == client_id).with_for_update()
        return self.db.scalar(query)

    def get_supplier_payment_allocation_for_update(
        self, allocation_id: int
    ) -> Optional[SupplierPaymentAllocation]:
        query = (
            select(SupplierPaymentAllocation)
            .options(
                joinedload(SupplierPaymentAllocation.movement),
                joinedload(SupplierPaymentAllocation.purchase_invoice),
                joinedload(SupplierPaymentAllocation.purchase_quote),
            )
            .where(SupplierPaymentAllocation.id == allocation_id)
        )
        return self.db.scalar(query)

    def get_client_payment_allocation_for_update(
        self, allocation_id: int
    ) -> Optional[ClientPaymentAllocation]:
        query = (
            select(ClientPaymentAllocation)
            .options(
                joinedload(ClientPaymentAllocation.movement),
                joinedload(ClientPaymentAllocation.sales_invoice),
                joinedload(ClientPaymentAllocation.sales_quote),
            )
            .where(ClientPaymentAllocation.id == allocation_id)
        )
        return self.db.scalar(query)

    def shift_balance_chain(
        self,
        model_cls: Type,
        entity_fk_name: str,
        entity_id: int,
        after_movement_id: int,
        delta,
    ) -> None:
        """
        Ajusta la cadena de saldos (balance_before/balance_after) de la cuenta corriente
        tras modificar o eliminar un cobro/pago.
        """
        if delta == 0:
            return

        query = (
            select(model_cls)
            .where(
                getattr(model_cls, entity_fk_name) == entity_id,
                model_cls.id > after_movement_id,
            )
            .order_by(model_cls.id.asc())
            .with_for_update()
        )
        rows = self.db.scalars(query).all()
        for row in rows:
            row.balance_before += delta
            row.balance_after += delta
            self.db.add(row)