from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload
from app.models.purchase_quote_item_model import PurchaseQuoteItem
from app.models.purchase_quote_model import PurchaseQuote
from app.schemas.purchase_quote_schema import PurchaseQuoteCreate, PurchaseQuoteUpdate

class PurchaseQuoteRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, purchase_quote_id: int) -> Optional[PurchaseQuote]:
        """
        Obtiene un presupuesto de compra con sus ítems, productos relacionados y creador.
        """
        query = (
            select(PurchaseQuote)
            .options(
                selectinload(PurchaseQuote.items).joinedload(PurchaseQuoteItem.product),
                joinedload(PurchaseQuote.creator),
            )
            .where(PurchaseQuote.id == purchase_quote_id)
        )
        return self.db.scalar(query)

    def get_item_by_id(self, item_id: int) -> Optional[PurchaseQuoteItem]:
        """
        Obtiene un ítem específico de un presupuesto de compra.
        """
        query = (
            select(PurchaseQuoteItem)
            .options(joinedload(PurchaseQuoteItem.product))
            .where(PurchaseQuoteItem.id == item_id)
        )
        return self.db.scalar(query)

    def get_active_by_supplier_and_date(
        self,
        supplier_id: int | None,
        supplier_name: str | None,
        quote_date,
    ) -> List[PurchaseQuote]:
        """
        Candidatos a duplicado: presupuestos no rechazados/vencidos del
        mismo proveedor (por id si está registrado, si no por nombre) y
        misma fecha.
        """
        query = (
            select(PurchaseQuote)
            .options(selectinload(PurchaseQuote.items))
            .where(PurchaseQuote.quote_date == quote_date)
            .where(PurchaseQuote.status.not_in(["rejected", "expired"]))
        )

        if supplier_id is not None:
            query = query.where(PurchaseQuote.supplier_id == supplier_id)
        elif supplier_name:
            query = query.where(
                PurchaseQuote.supplier_id.is_(None),
                PurchaseQuote.supplier_name.ilike(supplier_name.strip()),
            )
        else:
            return []

        return list(self.db.scalars(query).all())

    def get_purchase_quotes(
        self,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
        supplier_id: Optional[int] = None,
    ) -> Tuple[List[PurchaseQuote], int]:
        """
        Lista presupuestos de compra con paginación y filtros opcionales.
        """
        query = (
            select(PurchaseQuote)
            .options(
                selectinload(PurchaseQuote.items),
                joinedload(PurchaseQuote.creator),
            )
            .order_by(PurchaseQuote.id.desc())
        )

        if status:
            query = query.where(PurchaseQuote.status == status)

        if supplier_id:
            query = query.where(PurchaseQuote.supplier_id == supplier_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query) or 0

        query = query.offset((page - 1) * page_size).limit(page_size)
        items = self.db.scalars(query).unique().all()

        return list(items), total

    def create(
        self,
        *,
        obj_in: PurchaseQuoteCreate,
        supplier_snapshot: dict | None,
        total_amount: Decimal,
        items_data: list[dict],
        created_by: int | None,
    ) -> PurchaseQuote:
        """
        Crea la cabecera y los ítems del presupuesto de compra.
        """
        db_obj = PurchaseQuote(
            supplier_id=obj_in.supplier_id,
            supplier_name=obj_in.supplier_name,
            supplier_tax_id=obj_in.supplier_tax_id,
            supplier_snapshot=supplier_snapshot,
            quote_number=obj_in.quote_number,
            quote_date=obj_in.quote_date,
            valid_until=obj_in.valid_until,
            status="draft",
            notes=obj_in.notes,
            total_amount=total_amount,
            created_by=created_by,
        )
        self.db.add(db_obj)
        self.db.flush()

        for item in items_data:
            db_item = PurchaseQuoteItem(
                purchase_quote_id=db_obj.id,
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
        db_obj: PurchaseQuote,
        obj_in: PurchaseQuoteUpdate,
    ) -> PurchaseQuote:
        """
        Actualiza campos básicos del presupuesto de compra.
        """
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def link_item_to_product(
        self,
        item: PurchaseQuoteItem,
        product_id: int,
    ) -> PurchaseQuoteItem:
        """
        Vincula un ítem del presupuesto a un producto existente del catálogo.
        """
        item.product_id = product_id
        self.db.flush()
        self.db.refresh(item)
        return item

    def update_status(
        self,
        purchase_quote: PurchaseQuote,
        status_value: str,
    ) -> PurchaseQuote:
        """
        Cambia el estado del presupuesto de compra (draft/sent/approved/rejected/expired).
        """
        purchase_quote.status = status_value
        self.db.add(purchase_quote)
        self.db.flush()
        return purchase_quote