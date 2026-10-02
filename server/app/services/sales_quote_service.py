from datetime import date
from decimal import Decimal
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.constants.orders_constant import ORDER_DOCUMENT_SALES_QUOTE
from app.constants.sales_quote_constant import ALLOWED_SALES_QUOTE_STATUSES
from app.constants.account_movement_constant import ALLOWED_PAYMENT_METHODS
from app.constants.sales_type_constant import SalesType
from app.models.sales_quote_model import SalesQuote
from app.models.sales_rep_model import SalesRep
from app.repositories.client_repository import ClientRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.sales_quote_repository import SalesQuoteRepository
from app.schemas.sales_quote_schema import (
    ClientBranchSnapshot,
    ClientSnapshot,
    SalesQuoteCreate,
    SalesQuoteLinkProduct,
    SalesQuoteUpdate,
    SalesRepSnapshot,
)
from app.schemas.account_movement_schema import (
    ClientPaymentAllocationItem,
    ClientPaymentCreate,
    SalesQuotePaymentCreate,
    SalesQuotePaymentListResponse,
    SalesQuotePaymentResponse,
)
from app.services.client_account_movement_service import ClientAccountMovementService
from app.services.sales_document_payment_rules import (
    ensure_sales_document_accepts_payments,
)
from app.utils.import_matching import build_items_signature, is_same_document

class SalesQuoteService:
    """
    Presupuestos de venta. Dos usos (ver models/sales_quote_model.py):

    - Cotización suelta (order_id NULL): documento para cotizar a un cliente
      o consumidor final. No afecta stock ni cuenta corriente; solo cambia
      de estado (draft/sent/approved/rejected/expired/cancelled).

    - Documento de venta de un pedido (order_id NOT NULL): lo genera el
      pedido (create_from_order) cuando eligió document_type='sales_quote'.
      Nace 'approved', registra la deuda en la cuenta corriente del cliente
      y admite cobros imputados. Su estado lo maneja el pedido.
    """

    def __init__(self, db: Session):
        self.db = db
        self.sales_quote_repo = SalesQuoteRepository(db)
        self.product_repo = ProductRepository(db)
        self.client_repo = ClientRepository(db)
        self.order_repo = OrderRepository(db)
        self.client_account_movement_service = ClientAccountMovementService(db)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_quote_or_404(self, sales_quote_id: int) -> SalesQuote:
        quote = self.sales_quote_repo.get_by_id(sales_quote_id)
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Presupuesto de venta no encontrado",
            )
        return quote

    @staticmethod
    def _rep_snapshot(rep: SalesRep | None) -> dict | None:
        if rep is None:
            return None
        return SalesRepSnapshot(id=rep.id, name=rep.name, email=rep.email).model_dump()

    @staticmethod
    def _client_snapshot(client) -> dict:
        return ClientSnapshot(
            id=client.id,
            name=client.name,
            tax_id=client.tax_id,
        ).model_dump()

    @staticmethod
    def _branch_snapshot(branch) -> dict:
        return ClientBranchSnapshot(
            id=branch.id,
            name=branch.name,
            address=getattr(branch, "address", None),
            city=getattr(branch, "city", None),
        ).model_dump()

    @staticmethod
    def _sum_optional(values: list[Decimal | None]) -> Decimal | None:
        """Suma solo si TODOS los valores se conocen; si falta uno, None."""
        if any(v is None for v in values):
            return None
        return sum(values, Decimal("0.00"))

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def get_sales_quotes(
        self,
        page: int = 1,
        page_size: int = 10,
        status_value: Optional[str] = None,
        client_id: Optional[int] = None,
        from_orders: Optional[bool] = None,
    ):
        sales_quotes, total = self.sales_quote_repo.get_sales_quotes(
            page=max(1, page),
            page_size=max(1, page_size),
            status=status_value,
            client_id=client_id,
            only_from_orders=from_orders,
        )

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return {
            "sales_quotes": sales_quotes,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_by_id(self, sales_quote_id: int) -> SalesQuote:
        return self._get_quote_or_404(sales_quote_id)
    
    def get_online_payments(
        self,
        sales_quote_id: int,
    ) -> SalesQuotePaymentListResponse:
        quote = self.sales_quote_repo.get_by_id(sales_quote_id)

        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Presupuesto de venta no encontrado",
            )

        return self._build_online_payment_list_response(quote)

    # ------------------------------------------------------------------
    # Cotización suelta (alta manual / importada de PDF)
    # ------------------------------------------------------------------

    def create(self, data: SalesQuoteCreate, current_user: Optional[SalesRep]):
        # 1. Resolución de cliente (opcional: soporta consumidor final por nombre libre)
        client = None
        client_snapshot = None
        branch = None
        branch_snapshot = None

        if data.client_id:
            client = self.client_repo.get_by_id(data.client_id)
            if not client:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cliente no encontrado",
                )
            if not client.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El cliente está inactivo",
                )
            client_snapshot = self._client_snapshot(client)

        if data.client_branch_id:
            if client is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La sucursal requiere un cliente registrado",
                )
            branch = next(
                (b for b in client.branches if b.id == data.client_branch_id),
                None,
            )
            if branch is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La sucursal no pertenece al cliente o no existe",
                )
            if not branch.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La sucursal está inactiva",
                )
            branch_snapshot = self._branch_snapshot(branch)

        if not data.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El presupuesto debe tener al menos un ítem.",
            )

        # 2. Preparación de ítems y cálculo de totales
        items_data = []
        total_amount = Decimal("0.00")

        for item in data.items:
            product = None
            if item.product_id:
                product = self.product_repo.get_product_by_id(item.product_id)
                if not product:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Producto {item.product_id} no encontrado",
                    )
            else:
                # Vincular por SKU o nombre si no vino ya resuelto. No
                # afecta stock ni costo: un presupuesto es solo cotización.
                product = self.product_repo.find_by_sku_or_name(
                    item.product_sku, item.product_name
                )

            unit_price = Decimal(str(item.unit_price))
            subtotal = (unit_price * item.quantity)
            total_amount += subtotal

            # Costo: solo se conoce si el ítem está vinculado a un producto
            # que tiene costo cargado.
            unit_cost = None
            subtotal_cost = None
            margin = None
            if product is not None and product.unit_cost is not None:
                unit_cost = Decimal(str(product.unit_cost))
                subtotal_cost = unit_cost * item.quantity
                margin = subtotal - subtotal_cost

            items_data.append({
                "product_id": product.id if product is not None else None,
                "product_name": item.product_name.strip() if item.product_name else "Producto sin nombre",
                "product_brand": product.brand if product is not None else None,
                "product_sku": item.product_sku.strip() if item.product_sku else None,
                "quantity": item.quantity,
                "unit_cost": unit_cost,
                "unit_price": unit_price,
                "subtotal_cost": subtotal_cost,
                "subtotal": subtotal,
                "margin_amount": margin,
            })

        total_cost = self._sum_optional([i["subtotal_cost"] for i in items_data])
        margin_amount = (total_amount - total_cost) if total_cost is not None else None

        if client is not None and not data.force:
            self._raise_if_duplicate_sales_quote(
                client_id=client.id,
                quote_date=data.quote_date,
                items_data=items_data,
            )

        sales_rep_id = data.sales_rep_id or (current_user.id if current_user else None)
        sales_rep_snapshot = (
            self._rep_snapshot(current_user)
            if current_user and sales_rep_id == current_user.id
            else None
        )

        header = {
            "order_id": None,
            # Las cotizaciones sueltas las carga personal de la distribuidora.
            "sales_type": SalesType.B2B,
            "client_id": client.id if client else None,
            "client_branch_id": branch.id if branch else None,
            "sales_rep_id": sales_rep_id,
            "customer_name": client.name if client else (data.client_name or "Consumidor final"),
            "customer_tax_id": client.tax_id if client else data.client_tax_id,
            "customer_phone": client.phone if client else None,
            "customer_email": client.email if client else None,
            "client_snapshot": client_snapshot,
            "client_branch_snapshot": branch_snapshot,
            "sales_rep_snapshot": sales_rep_snapshot,
            "quote_number": data.quote_number,
            "quote_date": data.quote_date,
            "valid_until": data.valid_until,
            "status": "draft",
            "payment_method": data.payment_method,
            "notes": data.notes,
            "total_cost": total_cost,
            "total_amount": total_amount,
            "margin_amount": margin_amount,
        }

        return self.sales_quote_repo.create(header=header, items_data=items_data)

    def _raise_if_duplicate_sales_quote(
        self,
        *,
        client_id: int,
        quote_date,
        items_data: list[dict],
    ) -> None:
        candidates = self.sales_quote_repo.get_active_loose_by_client_and_date(
            client_id=client_id,
            quote_date=quote_date,
        )

        if not candidates:
            return

        candidate_signature = build_items_signature(items_data)

        for existing_quote in candidates:
            existing_signature = build_items_signature(
                {
                    "product_id": item.product_id,
                    "product_sku": item.product_sku,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                }
                for item in existing_quote.items
            )

            if is_same_document(candidate_signature, existing_signature):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Ya existe un presupuesto de venta activo con el "
                        f"mismo cliente, fecha ({quote_date}) y los mismos "
                        f"productos/cantidades (presupuesto #{existing_quote.id}). "
                        "Si de verdad es distinto, reenviá con force=true."
                    ),
                )

    def update(self, sales_quote_id: int, data: SalesQuoteUpdate) -> SalesQuote:
        quote = self._get_quote_or_404(sales_quote_id)
        return self.sales_quote_repo.update(db_obj=quote, obj_in=data)

    def register_online_payment(
        self,
        sales_quote_id: int,
        data: SalesQuotePaymentCreate,
        current_user: SalesRep | None,
    ) -> SalesQuotePaymentListResponse:
        """
        Registra un cobro sobre un presupuesto que nació de un pedido.

        El presupuesto registró su deuda en la cuenta corriente del cliente
        (movimiento 'invoice'), así que el cobro TIENE que descontarla: se
        delega en ClientAccountMovementService.register_payment con una
        imputación a este presupuesto. Así el movimiento 'payment', la
        imputación, paid_amount/payment_status y el saldo del cliente quedan
        siempre consistentes, y el cobro se puede editar o borrar desde el
        ledger de ventas a clientes.
        """
        if data.payment_method not in ALLOWED_PAYMENT_METHODS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Método de pago inválido",
            )

        quote = self._get_quote_or_404(sales_quote_id)

        if quote.client_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El presupuesto debe estar asociado a un cliente",
            )

        ensure_sales_document_accepts_payments(
            "sales_quote",
            quote,
            f"presupuesto #{quote.quote_number}",
        )

        self.client_account_movement_service.register_payment(
            client_id=quote.client_id,
            data=ClientPaymentCreate(
                amount=data.amount,
                payment_method=data.payment_method,
                notes=data.notes,
                allocations=[
                    ClientPaymentAllocationItem(
                        invoice_id=quote.id,
                        amount=data.amount,
                        document_type="sales_quote",
                    )
                ],
            ),
            current_user=current_user,
        )

        self.db.refresh(quote)

        return self._build_online_payment_list_response(quote)

    def _build_online_payment_list_response(
        self,
        quote: SalesQuote,
    ) -> SalesQuotePaymentListResponse:
        # Fuente única de verdad: las imputaciones de cobro del presupuesto
        # (ClientPaymentAllocation), las mismas que muestra el ledger.
        allocations = sorted(
            quote.payment_allocations,
            key=lambda alloc: alloc.id,
            reverse=True,
        )

        return SalesQuotePaymentListResponse(
            payments=[
                SalesQuotePaymentResponse(
                    id=alloc.id,
                    sales_quote_id=quote.id,
                    amount=alloc.amount_applied,
                    payment_method=alloc.movement.payment_method or "otro",
                    notes=alloc.movement.notes,
                    created_by=alloc.movement.created_by,
                    created_at=alloc.movement.created_at,
                )
                for alloc in allocations
            ],
            payment_status=quote.payment_status,
            paid_amount=quote.paid_amount,
            total_amount=quote.total_amount,
        )

    def link_item_to_product(
        self,
        sales_quote_id: int,
        item_id: int,
        data: SalesQuoteLinkProduct,
    ):
        quote = self._get_quote_or_404(sales_quote_id)
        item = self.sales_quote_repo.get_item_by_id(item_id)

        if not item or item.sales_quote_id != quote.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ítem no encontrado en este presupuesto",
            )

        product = self.product_repo.get_product_by_id(data.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado",
            )

        return self.sales_quote_repo.link_item_to_product(item, data.product_id)

    def update_status(
        self,
        sales_quote_id: int,
        status_value: str,
        current_user: Optional[SalesRep] = None,
    ) -> SalesQuote:
        quote = self._get_quote_or_404(sales_quote_id)
        status_value = status_value.lower()

        if status_value not in ALLOWED_SALES_QUOTE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estado inválido. Valores permitidos: {sorted(ALLOWED_SALES_QUOTE_STATUSES)}",
            )

        # Un presupuesto que nació de un pedido tiene efectos en cuenta
        # corriente: su ciclo de vida lo gobierna el pedido (cancelar el
        # pedido cancela el presupuesto y revierte la deuda).
        if quote.order_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Este presupuesto nació del pedido #{quote.order_id}: "
                    "su estado se gestiona desde el pedido."
                ),
            )

        return self.sales_quote_repo.update_status(quote, status_value)

    # ------------------------------------------------------------------
    # Presupuesto como documento de venta de un pedido
    # ------------------------------------------------------------------

    def create_from_order(
        self,
        order_id: int,
        current_user: Optional[SalesRep],
    ) -> SalesQuote:
        """
        Equivalente a SalesInvoiceService.create_from_order pero para
        pedidos con document_type='sales_quote'. Congela precios/costos del
        pedido, deja el presupuesto 'approved' y registra la deuda del
        cliente en su cuenta corriente.

        El stock NO se toca acá: ya lo consumió el pedido al confirmarse.
        """
        order = self.order_repo.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Orden no encontrada",
            )
        if order.document_type != ORDER_DOCUMENT_SALES_QUOTE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La orden no está configurada para generar un presupuesto de venta",
            )
        if not order.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La orden no tiene items",
            )
        if order.invoice_generated or self.sales_quote_repo.get_by_order_id(order.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La orden ya tiene un documento de venta generado",
            )
        if order.status not in ["confirmed", "preparing"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La orden debe estar confirmada o en preparación",
            )
        if order.client_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La orden {order.sales_type} no tiene cliente asociado",
            )

        client = self.client_repo.get_by_id(order.client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado",
            )
        if not client.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El cliente está inactivo",
            )

        items_data: list[dict] = []
        total_cost = Decimal("0.00")
        total_amount = Decimal("0.00")
        total_margin = Decimal("0.00")

        for item in order.items:
            unit_cost = Decimal(str(item.unit_cost))
            unit_price = Decimal(str(item.unit_price))
            subtotal_cost = Decimal(str(item.subtotal_cost))
            subtotal = Decimal(str(item.subtotal))
            margin_amount = Decimal(str(item.margin_amount))

            total_cost += subtotal_cost
            total_amount += subtotal
            total_margin += margin_amount

            items_data.append({
                "product_id": item.product_id,
                "product_name": item.product_name_snapshot,
                "product_brand": item.product_brand_snapshot,
                "product_sku": item.product_sku_snapshot,
                "quantity": item.quantity,
                "unit_cost": unit_cost,
                "unit_price": unit_price,
                "subtotal_cost": subtotal_cost,
                "subtotal": subtotal,
                "margin_amount": margin_amount,
            })

        sales_rep = current_user
        sales_rep_id = current_user.id if current_user else order.sales_rep_id
        sales_rep_snapshot = (
            self._rep_snapshot(sales_rep)
            if sales_rep is not None
            else (order.sales_rep_snapshot if isinstance(order.sales_rep_snapshot, dict) else None)
        )

        client_snapshot = (
            order.client_snapshot
            if isinstance(order.client_snapshot, dict)
            else self._client_snapshot(client)
        )
        branch_snapshot = (
            order.client_branch_snapshot
            if isinstance(order.client_branch_snapshot, dict)
            else None
        )

        header = {
            "order_id": order.id,
            "sales_type": order.sales_type,
            "client_id": order.client_id,
            "client_branch_id": order.client_branch_id,
            "sales_rep_id": sales_rep_id,
            "customer_name": order.customer_name or client.name,
            "customer_tax_id": order.customer_tax_id or client.tax_id,
            "customer_phone": order.customer_phone or client.phone,
            "customer_email": order.customer_email or client.email,
            "delivery_type": order.delivery_type,
            "delivery_address": order.delivery_address,
            "delivery_city": order.delivery_city,
            "delivery_reference": order.delivery_reference,
            "client_snapshot": client_snapshot,
            "client_branch_snapshot": branch_snapshot,
            "sales_rep_snapshot": sales_rep_snapshot,
            "quote_number": self.sales_quote_repo.generate_quote_number(),
            "quote_date": date.today(),
            "status": "approved",
            "payment_status": "pending",
            "paid_amount": Decimal("0.00"),
            "total_cost": total_cost,
            "total_amount": total_amount,
            "margin_amount": total_margin,
            "currency": getattr(order, "currency", None) or "ARS",
        }

        quote = self.sales_quote_repo.create(header=header, items_data=items_data)

        order.invoice_generated = True
        self.db.add(order)

        self._register_quote_receivable(quote, current_user)

        self.db.flush()
        self.db.refresh(quote)
        return quote

    def cancel_for_order(
        self,
        order_id: int,
        current_user: Optional[SalesRep] = None,
    ) -> SalesQuote | None:
        """
        Se llama cuando se cancela el pedido: cancela el presupuesto que
        había generado y revierte la deuda en la cuenta corriente.
        No mueve stock (lo repone el propio pedido).
        """
        quote = self.sales_quote_repo.get_by_order_id(order_id)

        if quote is None or quote.status == "cancelled":
            return quote

        # Igual que con los remitos: con cobros imputados no se cancela
        # sin antes revertirlos, para no descuadrar la cuenta corriente.
        if quote.paid_amount and quote.paid_amount > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "No se puede cancelar: el presupuesto ya tiene cobros "
                    "imputados. Borrá esos cobros desde el ledger de ventas a "
                    "clientes primero."
                ),
            )

        if quote.status == "approved" and quote.total_amount and quote.client_id is not None:
            self.client_account_movement_service.apply_movement(
                client_id=quote.client_id,
                movement_type="invoice_reversal",
                amount=quote.total_amount,
                reference_type="sales_quote",
                reference_id=quote.id,
                notes=f"Reversión por cancelación de presupuesto #{quote.quote_number}",
                created_by=current_user.id if current_user else None,
            )

        result = self.sales_quote_repo.update_status(quote, "cancelled")
        self.db.flush()
        self.db.refresh(result)
        return result

    def _register_quote_receivable(
        self,
        quote: SalesQuote,
        current_user: Optional[SalesRep],
    ) -> None:
        """
        Registra la deuda generada por el presupuesto en la cuenta corriente
        del cliente (mismo movimiento 'invoice' que un remito confirmado,
        con reference_type='sales_quote').
        """
        if not quote.total_amount or quote.client_id is None:
            return

        self.client_account_movement_service.apply_movement(
            client_id=quote.client_id,
            movement_type="invoice",
            amount=quote.total_amount,
            reference_type="sales_quote",
            reference_id=quote.id,
            notes=f"Presupuesto de venta #{quote.quote_number}",
            created_by=current_user.id if current_user else None,
        )
