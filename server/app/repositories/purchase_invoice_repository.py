from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload
from app.models.purchase_invoice_item_model import PurchaseInvoiceItem
from app.models.purchase_invoice_model import PurchaseInvoice
from app.schemas.purchase_invoice_schema import PurchaseInvoiceCreate, PurchaseInvoiceUpdate

class PurchaseInvoiceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, purchase_invoice_id: int) -> Optional[PurchaseInvoice]:
        """
        Obtiene un remito de compra con sus ítems, productos relacionados y creador.
        """
        query = (
            select(PurchaseInvoice)
            .options(
                selectinload(PurchaseInvoice.items).joinedload(PurchaseInvoiceItem.product),
                joinedload(PurchaseInvoice.creator),
            )
            .where(PurchaseInvoice.id == purchase_invoice_id)
        )
        return self.db.scalar(query)

    def get_by_ids(self, purchase_invoice_ids: List[int]) -> List[PurchaseInvoice]:
        """
        Trae varios remitos por id de una sola vez (para validar
        asignaciones de pago o enriquecer listados de movimientos).
        """
        if not purchase_invoice_ids:
            return []

        query = select(PurchaseInvoice).where(PurchaseInvoice.id.in_(purchase_invoice_ids))
        return list(self.db.scalars(query).all())

    def get_by_ids_for_update(self, purchase_invoice_ids: List[int]) -> List[PurchaseInvoice]:
        """
        Igual que get_by_ids pero con lock de fila, para actualizar
        paid_amount/payment_status de forma segura ante concurrencia.
        """
        if not purchase_invoice_ids:
            return []

        query = (
            select(PurchaseInvoice)
            .where(PurchaseInvoice.id.in_(purchase_invoice_ids))
            .with_for_update()
        )
        return list(self.db.scalars(query).all())

    def get_item_by_id(self, item_id: int) -> Optional[PurchaseInvoiceItem]:
        """
        Obtiene un ítem específico de un remito.
        """
        query = (
            select(PurchaseInvoiceItem)
            .options(joinedload(PurchaseInvoiceItem.product))
            .where(PurchaseInvoiceItem.id == item_id)
        )
        return self.db.scalar(query)

    def get_purchase_invoices(
        self,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
    ) -> Tuple[List[PurchaseInvoice], int]:
        """
        Lista remitos con paginación y filtro opcional por estado.
        """
        query = (
            select(PurchaseInvoice)
            .options(
                selectinload(PurchaseInvoice.items),
                joinedload(PurchaseInvoice.creator),
            )
            .order_by(PurchaseInvoice.id.desc())
        )

        if status:
            query = query.where(PurchaseInvoice.status == status)

        # Conteo total para paginación
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query) or 0

        # Aplicar paginación
        query = query.offset((page - 1) * page_size).limit(page_size)
        items = self.db.scalars(query).unique().all()

        return list(items), total

    def get_active_by_supplier_and_date(
        self,
        supplier_id: int | None,
        supplier_name: str | None,
        invoice_date,
    ) -> List[PurchaseInvoice]:
        """
        Candidatos a duplicado: remitos no cancelados del mismo proveedor
        (por id si está registrado, si no por nombre) y misma fecha.
        """
        query = (
            select(PurchaseInvoice)
            .options(selectinload(PurchaseInvoice.items))
            .where(PurchaseInvoice.invoice_date == invoice_date)
            .where(PurchaseInvoice.status != "cancelled")
        )

        if supplier_id is not None:
            query = query.where(PurchaseInvoice.supplier_id == supplier_id)
        elif supplier_name:
            query = query.where(
                PurchaseInvoice.supplier_id.is_(None),
                PurchaseInvoice.supplier_name.ilike(supplier_name.strip()),
            )
        else:
            return []

        return list(self.db.scalars(query).all())

    def get_pending_for_aging(self) -> List[PurchaseInvoice]:
        """
        Remitos de compra confirmados con saldo pendiente de pago
        (payment_status 'pending' o 'partial'), para calcular antigüedad
        de deuda con proveedores.
        """
        stmt = select(PurchaseInvoice).where(
            PurchaseInvoice.payment_status.in_(["pending", "partial"]),
            PurchaseInvoice.status != "cancelled",
        )
        return list(self.db.scalars(stmt).all())

    def create(
        self,
        *,
        obj_in: PurchaseInvoiceCreate,
        supplier_snapshot: dict | None,
        total_amount: Decimal,
        items_data: list[dict],
        created_by: int | None,
    ) -> PurchaseInvoice:
        """
        Crea la cabecera y los ítems del remito. 
        Usa flush() para obtener el ID sin finalizar la transacción.
        """
        db_obj = PurchaseInvoice(
            supplier_id=obj_in.supplier_id,
            supplier_name=obj_in.supplier_name,
            supplier_tax_id=obj_in.supplier_tax_id,
            supplier_snapshot=supplier_snapshot,
            invoice_number=obj_in.invoice_number,
            invoice_date=obj_in.invoice_date,
            status="draft",
            notes=obj_in.notes,
            total_amount=total_amount,
            created_by=created_by,
        )
        self.db.add(db_obj)
        self.db.flush()  # Genera ID para los ítems

        for item in items_data:
            db_item = PurchaseInvoiceItem(
                purchase_invoice_id=db_obj.id,
                product_id=item.get("product_id"),
                product_name=item["product_name"],
                product_sku=item.get("product_sku"),
                quantity=item["quantity"],
                unit_cost=item["unit_cost"],
                subtotal=item["subtotal"],
            )
            self.db.add(db_item)

        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def update(
        self,
        *,
        db_obj: PurchaseInvoice,
        obj_in: PurchaseInvoiceUpdate,
    ) -> PurchaseInvoice:
        """
        Actualiza campos básicos del remito.
        """
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def link_item_to_product(
        self,
        item: PurchaseInvoiceItem,
        product_id: int,
    ) -> PurchaseInvoiceItem:
        """
        Vincula un ítem de un remito a un producto existente del catálogo.
        """
        item.product_id = product_id
        self.db.flush()
        self.db.refresh(item)
        return item

    def update_status(
        self,
        purchase_invoice: PurchaseInvoice,
        status_value: str,
    ) -> PurchaseInvoice:
        """
        Cambia el estado del remito. 
        Nota: No hace commit para permitir que el Service maneje el stock atómicamente.
        """
        purchase_invoice.status = status_value
        self.db.add(purchase_invoice)
        self.db.flush()
        return purchase_invoice