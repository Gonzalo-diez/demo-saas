from decimal import Decimal
from sqlalchemy.orm import Session
from datetime import date
from app.constants.orders_constant import (
    ALLOWED_ORDER_STATUSES,
    ORDER_DOCUMENT_SALES_QUOTE,
    VALID_STATUS_TRANSITIONS,
)
from app.models.sales_rep_model import SalesRep
from app.models.client_model import Client
from app.models.order_model import Order
from app.schemas.order_schema import (
    OrderUpdateB2B,
    OrderUpdateShop,
    OrderCreateShop,
    OrderCreateB2B,
    OrderListResponse,
    OrderResponse,
    OrderUpdateStatus,
    OrderEditShop,
    OrderEditB2B,
)
from app.utils.normalize_text import normalize_text
from app.utils.category_normalizer import is_regulated_category
from app.models.order_item_model import OrderItem
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.client_repository import ClientRepository
from app.services.inventory_movement_service import InventoryMovementService
from app.services.sales_invoice_service import SalesInvoiceService
from app.services.sales_quote_service import SalesQuoteService
import app.services.email_service as email_service
import app.services.whatsapp_service as whatsapp_service

def _try_send_order_emails(order: Order) -> None:
    try:
        email_service.send_order_admin_email(order)
        order.email_last_sent_at = email_service.utcnow()

    except Exception as exc:
        print(f"[Email] admin error #{order.id}: {exc}")

    if order.customer_email:
        try:
            email_service.send_order_customer_email(order)
            order.email_last_sent_at = email_service.utcnow()

        except Exception as exc:
            print(f"[Email] customer error #{order.id}: {exc}")
            
def _try_send_order_status_whatsapp(order: Order, message: str) -> None:
    try:
        whatsapp_service.send_order_status_whatsapp(
            order,
            message,
        )
    except Exception as exc:
        print(
            f"[WhatsApp error #{order.id}]: {exc}"
        )


def _try_send_order_customer_whatsapp(order: Order) -> None:
    try:
        whatsapp_service.send_order_customer_whatsapp(order)
    except Exception as exc:
        print(f"[WhatsApp interactive error #{order.id}]: {exc}")

class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = OrderRepository(db)
        self.product_repo = ProductRepository(db)
        self.client_repo = ClientRepository(db)
        self.inventory_movement_service = InventoryMovementService(db)
        self.sales_invoice_service = SalesInvoiceService(db)
        self.sales_quote_service = SalesQuoteService(db)

    def _ensure_document_type_editable(self, order: Order, new_type: str | None) -> None:
        """El tipo de documento solo se cambia antes de que se genere."""
        if (
            new_type is not None
            and new_type != order.document_type
            and order.invoice_generated
        ):
            raise ValueError(
                "No se puede cambiar el tipo de documento: la orden ya generó su "
                "remito/presupuesto"
            )

    @staticmethod
    def _items_unchanged(order: Order, items_in: list) -> bool:
        """True si los ítems entrantes son exactamente los de la orden (mismos productos y cantidades)."""
        new_map = {i.product_id: i.quantity for i in items_in}
        if len(new_map) != len(items_in):
            return False
        old_map = {i.product_id: i.quantity for i in order.items}
        return new_map == old_map

    def _ensure_items_editable(self, order: Order, items_in: list) -> bool:
        """
        Una vez generado el remito/presupuesto (order.invoice_generated) la orden
        ya no puede cambiar ítems ni totales: el documento y la cuenta corriente
        quedarían desfasados. Devuelve True si hay que dejar los ítems tal cual
        (edición solo de datos de cabecera); levanta ValueError si intentan
        cambiarlos.
        """
        if not order.invoice_generated:
            return False

        if not self._items_unchanged(order, items_in):
            raise ValueError(
                "No se pueden modificar los ítems: la orden ya generó su "
                "remito/presupuesto. Cancelá la orden y creá una nueva."
            )
        return True

    def _prepare_branch_change(self, order: Order, new_branch_id: int | None) -> None:
        """
        Valida un cambio de sucursal y deja actualizado el snapshot de la orden.
        El repository se encarga de asignar client_branch_id.
        """
        if new_branch_id is None or new_branch_id == order.client_branch_id:
            return

        if order.client_id is None:
            raise ValueError("La orden no tiene cliente asociado: no admite sucursal")

        if order.invoice_generated:
            raise ValueError(
                "No se puede cambiar la sucursal: la orden ya generó su remito/presupuesto"
            )

        branch = self.client_repo.get_branch_by_id(new_branch_id)
        if not branch:
            raise ValueError("Sucursal no encontrada")
        if branch.client_id != order.client_id:
            raise ValueError("La sucursal no pertenece al cliente")
        if not branch.is_active:
            raise ValueError("La sucursal está inactiva")

        order.client_branch_snapshot = {
            "id": branch.id,
            "name": branch.name,
            "address": getattr(branch, "address", None),
            "city": getattr(branch, "city", None),
        }

    def _calculate_totals(self, items_in: list):
        product_ids = [i.product_id for i in items_in]
        
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("No se permiten productos duplicados")

        products = self.product_repo.get_products_by_ids(product_ids)
        products_map = {p.id: p for p in products}

        total_amount = Decimal("0.00")
        total_cost = Decimal("0.00")
        has_regulated_items = False

        items_out = []

        for item in items_in:
            product = products_map.get(item.product_id)

            if not product:
                raise ValueError(f"Producto {item.product_id} no existe")

            if not product.is_active:
                raise ValueError(f"Producto {product.name} inactivo")

            if is_regulated_category(product.category):
                has_regulated_items = True

            unit_price = product.unit_price or Decimal("0")
            unit_cost = product.unit_cost or Decimal("0")

            subtotal = unit_price * item.quantity
            subtotal_cost = unit_cost * item.quantity
            margin = subtotal - subtotal_cost

            items_out.append({
                "product_id": product.id,
                "product_name": product.name,
                "product_brand": product.brand,
                "product_sku": product.sku,
                "product_image_url": product.image_url,
                "quantity": item.quantity,
                "unit_price": unit_price,
                "unit_cost": unit_cost,
                "subtotal": subtotal,
                "subtotal_cost": subtotal_cost,
                "margin_amount": margin,
            })

            total_amount += subtotal
            total_cost += subtotal_cost

        return {
            "items": items_out,
            "total_amount": total_amount,
            "total_cost": total_cost,
            "margin_amount": total_amount - total_cost,
            "has_regulated_items": has_regulated_items,
        }
        
    def _apply_order_inventory_delta(
        self,
        order: Order,
        old_items: list[OrderItem],
        new_items_data,
    ) -> None:

        old_map = {
            item.product_id: item.quantity
            for item in old_items
        }

        new_map = {
            item.product_id: item.quantity
            for item in new_items_data
        }

        all_products = (
            set(old_map.keys())
            | set(new_map.keys())
        )

        for product_id in all_products:
            old_qty = old_map.get(product_id, 0)
            new_qty = new_map.get(product_id, 0)
            delta = new_qty - old_qty

            # Incrementó cantidad
            if delta > 0:
                self.inventory_movement_service.apply_movement(
                    product_id=product_id,
                    quantity=delta,
                    movement_type="sale",
                    reference_type="order",
                    reference_id=order.id,
                )

            # Redujo cantidad
            elif delta < 0:
                self.inventory_movement_service.apply_movement(
                    product_id=product_id,
                    quantity=abs(delta),
                    movement_type="sale_reversal",
                    reference_type="order",
                    reference_id=order.id,
                )

    def create_order_shop(self, *, obj_in: OrderCreateShop, current_client: Client) -> Order:
        total_data = self._calculate_totals(obj_in.items)

        # Verificación de edad para productos regulados (tabaco),
        # según Ley 26.687. El checkbox y el DNI son declarados por
        # el cliente; la verificación real del documento queda a
        # cargo de quien entrega el pedido.
        if total_data["has_regulated_items"] and not (obj_in.customer_dni and obj_in.age_confirmed):
            raise ValueError(
                "Este pedido incluye productos regulados (tabaco). "
                "Es obligatorio confirmar el DNI y declarar ser mayor de 18 años "
                "para poder completarlo."
            )

        # El pedido queda vinculado directamente al cliente logueado que
        # lo hizo (ya no se intenta adivinar por CUIT: solo compran
        # clientes registrados y autenticados).
        total_data["client_id"] = current_client.id
        total_data["client_snapshot"] = {
            "id": current_client.id,
            "name": current_client.name,
        }

        branch = None
        if obj_in.client_branch_id:
            branch = self.client_repo.get_branch_by_id(obj_in.client_branch_id)
            if not branch:
                raise ValueError("Sucursal no encontrada")
            if branch.client_id != current_client.id:
                raise ValueError("La sucursal no pertenece al cliente")

        total_data["client_branch_snapshot"] = {
            "id": branch.id,
            "name": branch.name,
            "address": getattr(branch, "address", None),
            "city": getattr(branch, "city", None),
        } if branch else None

        order = self.repo.create_order_shop(
            obj_in=obj_in,
            total_data=total_data,
        )

        self.db.commit()
        self.db.refresh(order) 
        _try_send_order_emails(order)
        return order

    def create_order_b2b(
        self, *, obj_in: OrderCreateB2B, current_user: SalesRep
    ) -> Order:
        client = self.client_repo.get_by_id(obj_in.client_id)
        if not client:
            raise ValueError("Cliente no encontrado")

        branch = None
        if obj_in.client_branch_id:
            branch = self.client_repo.get_branch_by_id(obj_in.client_branch_id)
            if not branch:
                raise ValueError("Sucursal no encontrada")
            if branch.client_id != client.id:
                raise ValueError("La sucursal no pertenece al cliente")

        total_data = self._calculate_totals(obj_in.items)

        # Agregar snapshots al total_data que espera el repo
        total_data["client_snapshot"] = {
            "id": client.id,
            "name": client.name,
        }
        total_data["client_branch_snapshot"] = {
            "id": branch.id,
            "name": branch.name,
            "address": getattr(branch, "address", None),
            "city": getattr(branch, "city", None),
        } if branch else None
        total_data["sales_rep_snapshot"] = {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
        }

        order = self.repo.create_order_b2b(
            obj_in=obj_in,
            sales_rep_id=current_user.id,
            total_data=total_data,
        )
        
        self.db.commit()
        self.db.refresh(order)

        return order

    def get_order(self, order_id: int) -> Order | None:
        return self.repo.get_order_by_id(order_id)

    def list_orders(
        self,
        status: str | None = None,
        sales_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> OrderListResponse:

        orders, total = self.repo.get_orders(
            status=status,
            sales_type=sales_type,
            page=page,
            page_size=page_size,
        )

        items = [OrderResponse.model_validate(o) for o in orders]

        return OrderListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def update_order_shop(self, order_id: int, obj_in: OrderUpdateShop) -> Order:
        order = self.repo.get_order_by_id(order_id)

        if not order:
            raise ValueError("Orden no encontrada")

        if order.status != "pending_confirmation":
            raise ValueError("No se puede editar una orden procesada")

        self._ensure_document_type_editable(order, obj_in.document_type)

        return self.repo.update_order_shop(db_obj=order, obj_in=obj_in)

    def update_order_b2b(self, order_id: int, obj_in: OrderUpdateB2B) -> Order:
        order = self.repo.get_order_by_id(order_id)

        if not order:
            raise ValueError("Orden no encontrada")

        self._ensure_document_type_editable(order, obj_in.document_type)
        self._prepare_branch_change(order, obj_in.client_branch_id)

        return self.repo.update_order_b2b(db_obj=order, obj_in=obj_in)

    def update_order_status(
        self,
        order_id: int,
        status: str,
        current_user: SalesRep | None = None,
    ) -> Order:
        order = self.repo.get_order_by_id(order_id)

        if not order:
            raise ValueError("Orden no encontrada")

        normalized = normalize_text(status)

        if not normalized:
            raise ValueError("Estado inválido")

        normalized = normalized.strip().lower()

        if normalized not in ALLOWED_ORDER_STATUSES:
            raise ValueError("Estado no permitido")

        current_status = (order.status or "").strip().lower()

        if normalized == current_status:
            return order

        allowed = VALID_STATUS_TRANSITIONS.get(
            current_status,
            set(),
        )

        if normalized not in allowed:
            raise ValueError("Transición inválida")

        # =========================
        # CONFIRMED → consumir stock
        # =========================

        if (
            normalized == "confirmed"
            and not order.stock_consumed
        ):
            for item in order.items:
                self.inventory_movement_service.apply_movement(
                    product_id=item.product_id,
                    movement_type="sale",
                    quantity=item.quantity,
                    reference_type="order",
                    reference_id=order.id,
                    notes=f"Salida por orden #{order.id}",
                )

            order.stock_consumed = True

        # =========================
        # PREPARING → generar remito
        # =========================

        # =========================
        # PREPARING → generar documento de venta
        # =========================

        if normalized == "preparing" and not order.invoice_generated:
            if order.document_type == ORDER_DOCUMENT_SALES_QUOTE:
                quote = self.sales_quote_service.create_from_order(
                    order_id=order.id,
                    current_user=current_user,
                )

                if order.customer_email:
                    try:
                        email_service.send_sales_quote_customer_email(
                            order=order,
                            quote=quote,
                        )
                        quote.pdf_generated_at = email_service.utcnow()
                        quote.email_sent_at = email_service.utcnow()
                    except Exception as exc:
                        print(f"[Email error #{order.id}]: {exc}")

            else:
                invoice = self.sales_invoice_service.create_from_order(
                    order_id=order.id,
                    current_user=current_user,
                )

                order.invoice_generated = True

                if invoice:
                    invoice = self.sales_invoice_service.update_status(
                        invoice.id,
                        "confirmed",
                        current_user,
                    )

                    if order.customer_email:
                        try:
                            email_service.send_invoice_customer_email(
                                order=order,
                                invoice=invoice,
                            )
                            invoice.pdf_generated_at = email_service.utcnow()
                            invoice.email_sent_at = email_service.utcnow()
                        except Exception as exc:
                            print(f"[Email error #{order.id}]: {exc}")
        # =========================
        # CANCELLED → Cancelar documentos y devolver stock
        # =========================
        if normalized == "cancelled":
            # 1. Cancelación del documento de venta generado
            if order.invoice_generated:
                if order.document_type == ORDER_DOCUMENT_SALES_QUOTE:
                    self.sales_quote_service.cancel_for_order(
                        order_id=order.id,
                        current_user=current_user,
                    )
                else:
                    # Caso Sales Invoice (Remito / Factura)
                    if order.sales_invoice and order.sales_invoice.status != "cancelled":
                        self.sales_invoice_service.update_status(
                            order.sales_invoice.id,
                            "cancelled",
                            current_user,
                        )

            # 2. Devolución de stock (si el pedido consumió inventario)
            if order.stock_consumed:
                for item in order.items:
                    self.inventory_movement_service.apply_movement(
                        product_id=item.product_id,
                        movement_type="adjustment_in",
                        quantity=item.quantity,
                        reference_type="order",
                        reference_id=order.id,
                        notes=f"Reposición por cancelación de orden #{order.id}",
                    )

                order.stock_consumed = False

        updated_order = self.repo.update_order_status(
            db_obj=order,
            obj_in=OrderUpdateStatus(
                status=normalized,
            ),
        )

        # =========================
        # WHATSAPP/EMAIL (side effect)
        # =========================

        try:
            if normalized == "confirmed":
                _try_send_order_customer_whatsapp(updated_order)
            
            if normalized == "shipped":
                _try_send_order_status_whatsapp(
                    updated_order,
                    f"Tu pedido #{updated_order.id} ha sido enviado.",
                )
                email_service.send_order_shipped_email(
                    updated_order
                )

            elif normalized == "delivered":
                _try_send_order_status_whatsapp(
                    updated_order,
                    f"Tu pedido #{updated_order.id} ha sido entregado.",
                )
                email_service.send_order_delivered_email(
                    updated_order
                )

        except Exception as exc:
            print(
                f"[Email error #{updated_order.id}]: {exc}"
            )

        return updated_order
    
    def schedule_delivery(
        self,
        order_id: int,
        scheduled_delivery_date: date,
    ) -> Order:

        order = self.repo.get_order_by_id(order_id)

        if not order:
            raise ValueError("Orden no encontrada")

        return self.repo.schedule_delivery(
            db_obj=order,
            scheduled_delivery_date=scheduled_delivery_date,
        )
    
    def edit_order_shop(
        self,
        order_id: int,
        obj_in: OrderEditShop,
    ) -> Order:

        order = self.repo.get_order_by_id_for_update(order_id)

        if not order:
            raise ValueError("Orden no encontrada")

        if order.status in {
            "shipped",
            "delivered",
            "cancelled",
        }:
            raise ValueError(
                "La orden no puede editarse"
            )

        keep_items = self._ensure_items_editable(order, obj_in.items)

        old_items = list(order.items)

        total_data = None if keep_items else self._calculate_totals(obj_in.items)

        stock_affecting_statuses = {
            "confirmed",
            "preparing",
        }

        if not keep_items and order.status in stock_affecting_statuses:

            self._apply_order_inventory_delta(
                order=order,
                old_items=old_items,
                new_items_data=obj_in.items,
            )

        return self.repo.edit_order_shop(
            db_obj=order,
            obj_in=obj_in,
            total_data=total_data,
        )

    def edit_order_b2b(
        self,
        order_id: int,
        obj_in: OrderEditB2B,
    ) -> Order:

        order = self.repo.get_order_by_id_for_update(order_id)

        if not order:
            raise ValueError("Orden no encontrada")

        if order.status in {
            "shipped",
            "delivered",
            "cancelled",
        }:
            raise ValueError(
                "La orden no puede editarse"
            )

        keep_items = self._ensure_items_editable(order, obj_in.items)
        self._prepare_branch_change(order, obj_in.client_branch_id)

        old_items = list(order.items)

        total_data = None if keep_items else self._calculate_totals(obj_in.items)

        stock_affecting_statuses = {
            "confirmed",
            "preparing",
        }

        if not keep_items and order.status in stock_affecting_statuses:

            self._apply_order_inventory_delta(
                order=order,
                old_items=old_items,
                new_items_data=obj_in.items,
            )

        return self.repo.edit_order_b2b(
            db_obj=order,
            obj_in=obj_in,
            total_data=total_data,
        )