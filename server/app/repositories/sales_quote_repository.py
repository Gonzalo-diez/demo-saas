from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload
from app.models.sales_quote_item_model import SalesQuoteItem
from app.models.sales_quote_model import SalesQuote
from app.schemas.sales_quote_schema import SalesQuoteUpdate

class SalesQuoteRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_item_rows_for_clients(
        self,
        client_ids: list[int],
    ) -> List[tuple]:
        """
        (client_id, product_id, quantity, unit_price) de cada ítem de
        presupuestos de venta activos para esos clientes. Ver
        SalesInvoiceRepository.get_item_rows_for_clients: mismo propósito,
        para cuando la cuenta corriente se importa como presupuestos.
        """
        if not client_ids:
            return []

        query = (
            select(
                SalesQuote.client_id,
                SalesQuoteItem.product_id,
                SalesQuoteItem.quantity,
                SalesQuoteItem.unit_price,
            )
            .join(SalesQuoteItem, SalesQuoteItem.sales_quote_id == SalesQuote.id)
            .where(SalesQuote.client_id.in_(client_ids))
            .where(SalesQuote.status.not_in(["rejected", "expired", "cancelled"]))
        )
        return list(self.db.execute(query).all())

    def get_by_id(self, sales_quote_id: int) -> Optional[SalesQuote]:
        """
        Obtiene un presupuesto de venta con sus ítems, productos relacionados y vendedor.
        """
        query = (
            select(SalesQuote)
            .options(
                selectinload(SalesQuote.items).joinedload(SalesQuoteItem.product),
                joinedload(SalesQuote.sales_rep),
            )
            .where(SalesQuote.id == sales_quote_id)
        )
        return self.db.scalar(query)

    def get_by_order_id(self, order_id: int) -> Optional[SalesQuote]:
        """
        Presupuesto generado por un pedido (a lo sumo uno: uq_sales_quote_order_id).
        """
        query = (
            select(SalesQuote)
            .options(
                selectinload(SalesQuote.items),
                joinedload(SalesQuote.sales_rep),
            )
            .where(SalesQuote.order_id == order_id)
        )
        return self.db.scalar(query)

    def get_active_loose_by_client_and_date(
        self,
        client_id: int,
        quote_date,
    ) -> List[SalesQuote]:
        """
        Candidatos a duplicado entre presupuestos sueltos (order_id NULL,
        no generados por un pedido) del mismo cliente y misma fecha.
        """
        query = (
            select(SalesQuote)
            .options(selectinload(SalesQuote.items))
            .where(SalesQuote.client_id == client_id)
            .where(SalesQuote.quote_date == quote_date)
            .where(SalesQuote.order_id.is_(None))
            .where(SalesQuote.status.not_in(["rejected", "expired", "cancelled"]))
        )
        return list(self.db.scalars(query).all())

    def get_by_ids(self, sales_quote_ids: List[int]) -> List[SalesQuote]:
        """
        Trae varios presupuestos por id de una sola vez (para validar
        asignaciones de pago o enriquecer listados de movimientos).
        """
        if not sales_quote_ids:
            return []

        query = select(SalesQuote).where(SalesQuote.id.in_(sales_quote_ids))
        return list(self.db.scalars(query).all())

    def get_by_ids_for_update(self, sales_quote_ids: List[int]) -> List[SalesQuote]:
        """
        Igual que get_by_ids pero con lock de fila, para actualizar
        paid_amount/payment_status de forma segura ante concurrencia.
        """
        if not sales_quote_ids:
            return []

        query = (
            select(SalesQuote)
            .where(SalesQuote.id.in_(sales_quote_ids))
            .with_for_update()
        )
        return list(self.db.scalars(query).all())

    def get_item_by_id(self, item_id: int) -> Optional[SalesQuoteItem]:
        """
        Obtiene un ítem específico de un presupuesto de venta.
        """
        query = (
            select(SalesQuoteItem)
            .options(joinedload(SalesQuoteItem.product))
            .where(SalesQuoteItem.id == item_id)
        )
        return self.db.scalar(query)

    def get_sales_quotes(
        self,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
        client_id: Optional[int] = None,
        only_from_orders: Optional[bool] = None,
    ) -> Tuple[List[SalesQuote], int]:
        """
        Lista presupuestos de venta con paginación y filtros opcionales.

        only_from_orders: True = solo los que nacieron de un pedido,
        False = solo cotizaciones sueltas, None = todos.
        """
        query = (
            select(SalesQuote)
            .options(
                selectinload(SalesQuote.items),
                joinedload(SalesQuote.sales_rep),
            )
            .order_by(SalesQuote.id.desc())
        )

        if status:
            query = query.where(SalesQuote.status == status)

        if client_id:
            query = query.where(SalesQuote.client_id == client_id)

        if only_from_orders is True:
            query = query.where(SalesQuote.order_id.is_not(None))
        elif only_from_orders is False:
            query = query.where(SalesQuote.order_id.is_(None))

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query) or 0

        query = query.offset((page - 1) * page_size).limit(page_size)
        items = self.db.scalars(query).unique().all()

        return list(items), total

    def get_pending_for_aging(self) -> List[SalesQuote]:
        """
        Presupuestos que nacieron de un pedido, siguen vigentes y tienen
        saldo pendiente de cobro (payment_status 'pending' o 'partial'),
        para calcular antigüedad de deuda de clientes. Las cotizaciones
        sueltas (order_id NULL) no generan deuda y quedan afuera.
        """
        stmt = select(SalesQuote).where(
            SalesQuote.order_id.is_not(None),
            SalesQuote.status == "approved",
            SalesQuote.payment_status.in_(["pending", "partial"]),
            SalesQuote.client_id.is_not(None),
        )
        return list(self.db.scalars(stmt).all())

    def generate_quote_number(self, prefix: str = "PRE", punto_venta: int = 1) -> str:
        """
        Próximo número correlativo de presupuesto generado por el sistema.

        Formato: PRE-0001-00000042 (el prefijo lo distingue de los remitos,
        que usan 0001-00000042). Los números que cargan a mano o vienen de
        un PDF no siguen este formato y se ignoran al calcular el máximo.
        """
        head = f"{prefix}-{punto_venta:04d}-"

        stmt = (
            select(SalesQuote.quote_number)
            .where(SalesQuote.quote_number.like(f"{head}%"))
            .with_for_update()
        )
        existing = self.db.scalars(stmt).all()

        max_correlativo = 0
        for number in existing:
            try:
                correlativo = int(number.rsplit("-", 1)[1])
                if correlativo > max_correlativo:
                    max_correlativo = correlativo
            except (IndexError, ValueError):
                continue

        return f"{head}{max_correlativo + 1:08d}"

    def create(
        self,
        *,
        header: dict,
        items_data: list[dict],
    ) -> SalesQuote:
        """
        Crea la cabecera y los ítems de un presupuesto de venta.

        `header` trae las columnas de SalesQuote ya resueltas por el
        service (sea una cotización suelta o un presupuesto de pedido).
        """
        db_obj = SalesQuote(**header)
        self.db.add(db_obj)
        self.db.flush()

        for item in items_data:
            db_item = SalesQuoteItem(
                sales_quote_id=db_obj.id,
                product_id=item.get("product_id"),
                product_name=item["product_name"],
                product_brand=item.get("product_brand"),
                product_sku=item.get("product_sku"),
                quantity=item["quantity"],
                unit_cost=item.get("unit_cost"),
                unit_price=item["unit_price"],
                subtotal_cost=item.get("subtotal_cost"),
                subtotal=item["subtotal"],
                margin_amount=item.get("margin_amount"),
            )
            self.db.add(db_item)

        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def update(
        self,
        *,
        db_obj: SalesQuote,
        obj_in: SalesQuoteUpdate,
    ) -> SalesQuote:
        """
        Actualiza campos básicos del presupuesto de venta.
        """
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def link_item_to_product(
        self,
        item: SalesQuoteItem,
        product_id: int,
    ) -> SalesQuoteItem:
        """
        Vincula un ítem del presupuesto a un producto existente del catálogo.
        """
        item.product_id = product_id
        self.db.flush()
        self.db.refresh(item)
        return item

    def update_status(
        self,
        sales_quote: SalesQuote,
        status_value: str,
    ) -> SalesQuote:
        """
        Cambia el estado del presupuesto de venta
        (draft/sent/approved/rejected/expired/cancelled).
        """
        sales_quote.status = status_value
        self.db.add(sales_quote)
        self.db.flush()
        return sales_quote
