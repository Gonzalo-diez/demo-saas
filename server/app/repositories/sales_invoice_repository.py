from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload
from app.models.sales_invoice_item_model import SalesInvoiceItem
from app.models.sales_invoice_model import SalesInvoice
from app.schemas.sales_invoice_schema import SalesInvoiceCreate, SalesInvoiceUpdate
from app.constants.sales_invoice_constant import VALID_SALES_INVOICE_STATUS_TRANSITIONS

class SalesInvoiceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_item_rows_for_clients(
        self,
        client_ids: list[int],
    ) -> List[tuple]:
        """
        (client_id, product_id, quantity, unit_price) de cada ítem de
        remitos de venta activos para esos clientes. Se usa para detectar,
        fila por fila, qué ventas de una planilla de cuenta corriente ya
        fueron importadas antes (la planilla suele acumular filas viejas y
        nuevas mezcladas).
        """
        if not client_ids:
            return []

        query = (
            select(
                SalesInvoice.client_id,
                SalesInvoiceItem.product_id,
                SalesInvoiceItem.quantity,
                SalesInvoiceItem.unit_price,
            )
            .join(SalesInvoiceItem, SalesInvoiceItem.sales_invoice_id == SalesInvoice.id)
            .where(SalesInvoice.client_id.in_(client_ids))
            .where(SalesInvoice.status != "cancelled")
        )
        return list(self.db.execute(query).all())

    def get_by_id(self, sales_invoice_id: int) -> Optional[SalesInvoice]:
        """
        Obtiene un remito de venta con todas sus relaciones cargadas.
        """
        query = (
            select(SalesInvoice)
            .options(
                joinedload(SalesInvoice.client),
                joinedload(SalesInvoice.client_branch),
                joinedload(SalesInvoice.sales_rep),
                joinedload(SalesInvoice.order),
                selectinload(SalesInvoice.items).joinedload(SalesInvoiceItem.product),
            )
            .where(SalesInvoice.id == sales_invoice_id)
        )
        return self.db.scalar(query)

    def get_by_ids(self, sales_invoice_ids: List[int]) -> List[SalesInvoice]:
        """
        Trae varios remitos por id de una sola vez (para validar
        asignaciones de pago o enriquecer listados de movimientos).
        """
        if not sales_invoice_ids:
            return []

        query = select(SalesInvoice).where(SalesInvoice.id.in_(sales_invoice_ids))
        return list(self.db.scalars(query).all())

    def get_by_ids_for_update(self, sales_invoice_ids: List[int]) -> List[SalesInvoice]:
        """
        Igual que get_by_ids pero con lock de fila, para actualizar
        paid_amount/payment_status de forma segura ante concurrencia.
        """
        if not sales_invoice_ids:
            return []

        query = (
            select(SalesInvoice)
            .where(SalesInvoice.id.in_(sales_invoice_ids))
            .with_for_update()
        )
        return list(self.db.scalars(query).all())

    def get_active_by_client_and_date(
        self,
        client_id: int,
        invoice_date,
    ) -> List[SalesInvoice]:
        """
        Candidatos a duplicado: remitos de venta no cancelados del mismo
        cliente y misma fecha (para detectar reimportes accidentales).
        """
        query = (
            select(SalesInvoice)
            .options(selectinload(SalesInvoice.items))
            .where(SalesInvoice.client_id == client_id)
            .where(SalesInvoice.invoice_date == invoice_date)
            .where(SalesInvoice.status != "cancelled")
        )
        return list(self.db.scalars(query).all())

    def get_sales_invoices(
        self,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
    ) -> Tuple[List[SalesInvoice], int]:
        """
        Lista remitos de venta con paginación y filtro por estado.
        """
        query = (
            select(SalesInvoice)
            .options(
                joinedload(SalesInvoice.client),
                joinedload(SalesInvoice.sales_rep),
                selectinload(SalesInvoice.items),
            )
            .order_by(SalesInvoice.id.desc())
        )

        if status:
            query = query.where(SalesInvoice.status == status)

        # Conteo total
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query) or 0

        # Paginación
        query = query.offset((page - 1) * page_size).limit(page_size)
        items = self.db.scalars(query).unique().all()

        return list(items), total

    def get_pending_for_aging(self) -> List[SalesInvoice]:
        """
        Remitos de venta confirmados con saldo pendiente de cobro
        (payment_status 'pending' o 'partial'), para calcular antigüedad
        de deuda de clientes.
        """
        stmt = select(SalesInvoice).where(
            SalesInvoice.payment_status.in_(["pending", "partial"]),
            SalesInvoice.status != "cancelled",
            SalesInvoice.client_id.is_not(None),
        )
        return list(self.db.scalars(stmt).all())

    def create(
        self,
        *,
        obj_in: SalesInvoiceCreate,
        total_cost: Decimal,
        total_amount: Decimal,
        margin_amount: Decimal,
        items_data: list[dict],
        sales_rep_id: int,
        client_snapshot: dict | None,
        client_branch_snapshot: dict | None,
        sales_rep_snapshot: dict | None,
    ) -> SalesInvoice:
        """
        Crea cabecera e ítems de remito de venta.
        """
        db_obj = SalesInvoice(
            order_id=obj_in.order_id,
            client_id=obj_in.client_id,
            client_branch_id=obj_in.client_branch_id,
            client_snapshot=client_snapshot,
            client_branch_snapshot=client_branch_snapshot,
            sales_rep_id=sales_rep_id,
            sales_rep_snapshot=sales_rep_snapshot,
            invoice_number=obj_in.invoice_number,
            sales_type=obj_in.sales_type,
            invoice_date=obj_in.invoice_date,
            customer_name=obj_in.customer_name,
            customer_phone=obj_in.customer_phone,
            customer_email=obj_in.customer_email,
            delivery_address=obj_in.delivery_address,
            delivery_city=obj_in.delivery_city,
            delivery_reference=obj_in.delivery_reference,
            delivery_type=obj_in.delivery_type,
            currency=obj_in.currency,
            status="draft",
            notes=obj_in.notes,
            total_cost=total_cost,
            total_amount=total_amount,
            margin_amount=margin_amount,
        )
        self.db.add(db_obj)
        self.db.flush()

        for item in items_data:
            db_item = SalesInvoiceItem(
                sales_invoice_id=db_obj.id,
                product_id=item["product_id"],
                product_name=item.get("product_name"),
                product_brand=item.get("product_brand"),
                product_sku=item.get("product_sku"),
                product_snapshot=item.get("product_snapshot"),
                quantity=item["quantity"],
                unit_cost=item["unit_cost"],
                unit_price=item["unit_price"],
                subtotal_cost=item["subtotal_cost"],
                subtotal=item["subtotal"],
                margin_amount=item["margin_amount"],
            )
            self.db.add(db_item)

        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj
    
    def generate_invoice_number(self, punto_venta: int = 1) -> str:
        """
        Genera el próximo número de remito correlativo para un punto de venta.

        Formato AFIP: XXXX-XXXXXXXX
        Ejemplo:      0001-00000042

        Busca el máximo número correlativo ya usado para ese punto de venta
        y devuelve el siguiente. Thread-safe dentro de la misma transacción
        porque el INSERT posterior tiene un UNIQUE constraint que actúa
        como lock final.
        """
        prefix = f"{punto_venta:04d}-"

        # Buscar todos los invoice_number que pertenecen a este punto de venta
        stmt = (
            select(SalesInvoice.invoice_number)
            .where(SalesInvoice.invoice_number.like(f"{prefix}%"))
            .with_for_update()          # lock de lectura para evitar race condition
        )

        existing = self.db.scalars(stmt).all()

        max_correlativo = 0

        for number in existing:
            try:
                correlativo = int(number.split("-")[1])
                if correlativo > max_correlativo:
                    max_correlativo = correlativo
            except (IndexError, ValueError):
                continue

        next_correlativo = max_correlativo + 1

        return f"{punto_venta:04d}-{next_correlativo:08d}"

    def update(
        self,
        *,
        db_obj: SalesInvoice,
        obj_in: SalesInvoiceUpdate,
    ) -> SalesInvoice:
        if db_obj.status == "cancelled":
            raise ValueError(
                "No se puede editar un remito cancelado"
            )

        if obj_in.client_branch_id is not None:
            db_obj.client_branch_id = obj_in.client_branch_id

        if obj_in.customer_name is not None:
            db_obj.customer_name = obj_in.customer_name

        if obj_in.customer_phone is not None:
            db_obj.customer_phone = obj_in.customer_phone

        if obj_in.customer_email is not None:
            db_obj.customer_email = obj_in.customer_email

        if obj_in.delivery_type is not None:
            db_obj.delivery_type = obj_in.delivery_type

        if obj_in.delivery_address is not None:
            db_obj.delivery_address = obj_in.delivery_address

        if obj_in.delivery_city is not None:
            db_obj.delivery_city = obj_in.delivery_city

        if obj_in.delivery_reference is not None:
            db_obj.delivery_reference = obj_in.delivery_reference

        if obj_in.invoice_number is not None:
            db_obj.invoice_number = obj_in.invoice_number

        if obj_in.invoice_date is not None:
            db_obj.invoice_date = obj_in.invoice_date

        if obj_in.notes is not None:
            db_obj.notes = obj_in.notes

        self.db.flush()
        self.db.refresh(db_obj)

        return db_obj

    def update_status(
        self,
        *,
        sales_invoice: SalesInvoice,
        status_value: str,
    ) -> SalesInvoice:
        
        allowed = VALID_SALES_INVOICE_STATUS_TRANSITIONS.get(
            sales_invoice.status,
            set(),
        )

        if status_value not in allowed:
            raise ValueError(
                f"No se puede pasar de "
                f"{sales_invoice.status} a {status_value}"
            )

        sales_invoice.status = status_value

        self.db.add(sales_invoice)
        self.db.flush()

        return sales_invoice