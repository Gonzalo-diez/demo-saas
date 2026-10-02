from collections import Counter
from datetime import date
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.constants.account_movement_constant import ALLOWED_PAYMENT_METHODS
from app.constants.sales_invoice_constant import ALLOWED_SALES_INVOICE_STATUSES
from app.models.sales_rep_model import SalesRep
from app.repositories.client_repository import ClientRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.sales_invoice_repository import SalesInvoiceRepository
from app.repositories.sales_invoice_payment_repository import SalesInvoicePaymentRepository
from app.schemas.account_movement_schema import (
    SalesInvoicePaymentCreate,
    SalesInvoicePaymentListResponse,
    SalesInvoicePaymentResponse,
)
from app.schemas.sales_invoice_schema import ClientBranchSnapshot, ClientSnapshot, SalesInvoiceCreate, SalesInvoiceItemCreate, SalesInvoiceUpdate, SalesRepSnapshot
from app.constants.sales_type_constant import SalesType
from app.models.sales_invoice_model import SalesInvoice
from app.services.inventory_movement_service import InventoryMovementService
from app.services.client_account_movement_service import ClientAccountMovementService
from app.utils.import_matching import build_items_signature, is_same_document

class SalesInvoiceService:
    def __init__(self, db: Session):
        self.db = db
        self.sales_invoice_repo = SalesInvoiceRepository(db)
        self.client_repo = ClientRepository(db)
        self.product_repo = ProductRepository(db)
        self.order_repo = OrderRepository(db)
        self.inventory_movement_service = InventoryMovementService(db)
        self.client_account_movement_service = ClientAccountMovementService(db)
        self.sales_invoice_payment_repo = SalesInvoicePaymentRepository(db)
        
    def _validate_order_link(
        self,
        order_id: int,
        client_id: int | None,
        client_branch_id: int | None,
        invoice_items_counter: Counter,
        sales_type: SalesType,
        check_invoice_generated: bool = True,
    ) -> None:
        order = self.order_repo.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Orden asociada no encontrada",
            )

        # Validar cliente y sucursal solo en B2B
        # En ONLINE ambos son None tanto en la orden como en el remito — pasa solo
        if order.sales_type != sales_type.value:
            raise HTTPException(
                status_code=400,
                detail="El tipo de venta de la factura no coincide con el de la orden",
            )

        if order.client_id != client_id:
            raise HTTPException(
                status_code=400,
                detail="El cliente de la factura no coincide con el cliente de la orden",
            )

        if sales_type == SalesType.B2B:
            if order.client_id is None:
                raise HTTPException(
                    status_code=400,
                    detail="Una orden B2B debe tener un cliente asociado",
                )

            if order.client_branch_id != client_branch_id:
                raise HTTPException(
                    status_code=400,
                    detail="La sucursal de la factura no coincide con la de la orden",
                )

        # Verificar que la orden no tenga ya un remito.
        # Esto solo aplica cuando se está CREANDO un remito nuevo para la
        # orden (create()): ahí sí queremos evitar duplicarlo. No aplica
        # cuando se está confirmando (update_status) el remito que la
        # propia orden acaba de generar en create_from_order(), porque en
        # ese punto `invoice_generated` ya está en True a propósito y no
        # es un duplicado.
        if check_invoice_generated and order.invoice_generated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La orden ya tiene un remito generada",
            )

        # Items deben coincidir exactamente en ambos casos
        order_items_counter = Counter(
            {item.product_id: item.quantity for item in order.items}
        )
        if order_items_counter != invoice_items_counter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Los items del remito no coinciden con los de la orden asociada",
            )
            
    def _build_sales_rep_snapshot(self, sales_rep: SalesRep) -> dict:
        return SalesRepSnapshot(
            id=sales_rep.id,
            name=sales_rep.name,
            email=sales_rep.email,
        ).model_dump()
        
    def _build_client_snapshot(self, client) -> dict:
        return ClientSnapshot(
            id=client.id,
            name=client.name,
        ).model_dump()
        
    def _build_branch_snapshot(self, branch) -> dict:
        return ClientBranchSnapshot(
            id=branch.id,
            name=branch.name,
            address=getattr(branch, "address", None),
            city=getattr(branch, "city", None),
        ).model_dump()

    def get_by_id(self, sales_invoice_id: int):
        sales_invoice = self.sales_invoice_repo.get_by_id(sales_invoice_id)
        if not sales_invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Remito de venta no encontrado",
            )
        return sales_invoice

    def get_sales_invoices(
        self,
        page: int = 1,
        page_size: int = 10,
        status_value: str | None = None,
    ):
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

        if (
            status_value is not None
            and status_value not in ALLOWED_SALES_INVOICE_STATUSES
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estado de remito de venta inválido",
            )

        sales_invoices, total = self.sales_invoice_repo.get_sales_invoices(
            page=page,
            page_size=page_size,
            status=status_value,
        )

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return {
            "sales_invoices": sales_invoices,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def _raise_if_duplicate_sales_invoice(
        self,
        *,
        client_id: int,
        invoice_date: date,
        items_data: list[dict],
    ) -> None:
        candidates = self.sales_invoice_repo.get_active_by_client_and_date(
            client_id=client_id,
            invoice_date=invoice_date,
        )

        if not candidates:
            return

        candidate_signature = build_items_signature(items_data)

        for existing_invoice in candidates:
            existing_signature = build_items_signature(
                {
                    "product_id": item.product_id,
                    "product_sku": item.product_sku,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                }
                for item in existing_invoice.items
            )

            if is_same_document(candidate_signature, existing_signature):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Ya existe un remito de venta activo con el mismo "
                        f"cliente, fecha ({invoice_date}) y los mismos "
                        f"productos/cantidades (remito #{existing_invoice.id}, "
                        f"'{existing_invoice.invoice_number}'). Si de verdad "
                        "es un remito distinto, reenviá con force=true."
                    ),
                )

    def create(self, obj_in: SalesInvoiceCreate, current_user: SalesRep):
        client = None
        branch = None

        if obj_in.client_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Los remitos {obj_in.sales_type} requieren un cliente asociado",
            )

        client = self.client_repo.get_by_id(obj_in.client_id)
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

        if obj_in.sales_type == SalesType.B2B:
            if obj_in.client_branch_id is not None:
                branch = next(
                    (b for b in client.branches if b.id == obj_in.client_branch_id),
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
        else:
            # Los remitos ONLINE ya no tienen sucursal ni comprador anónimo:
            # siempre son de un Client logueado.
            obj_in.client_branch_id = None

        if not obj_in.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El remito debe tener al menos un item",
            )

        if obj_in.order_id is not None:
            invoice_counter = Counter(
                {item.product_id: item.quantity for item in obj_in.items}
            )
            self._validate_order_link(
                obj_in.order_id,
                obj_in.client_id,
                obj_in.client_branch_id,
                invoice_counter,
                obj_in.sales_type,
            )

        items_data: list[dict] = []
        total_cost = Decimal("0.00")
        total_amount = Decimal("0.00")
        total_margin = Decimal("0.00")

        for item in obj_in.items:
            product = (
                self.product_repo.get_product_by_id(item.product_id)
                if item.product_id
                else None
            )
            if not product:
                product = self.product_repo.find_by_sku_or_name(
                    item.product_sku, item.product_name
                )
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Producto con nombre {item.product_name} no encontrado",
                )
            if not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El producto {product.name} está inactivo",
                )
            if product.unit_price is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El producto {product.name} no tiene precio de venta definido",
                )

            unit_cost = Decimal(str(product.unit_cost or 0))
            unit_price = Decimal(str(product.unit_price))
            subtotal_cost = unit_cost * item.quantity
            subtotal = unit_price * item.quantity
            margin = subtotal - subtotal_cost

            total_cost += subtotal_cost
            total_amount += subtotal
            total_margin += margin

            items_data.append({
                "product_id": product.id,
                "product_name": product.name,
                "product_brand": product.brand,
                "product_sku": product.sku,
                "quantity": item.quantity,
                "unit_cost": unit_cost,
                "unit_price": unit_price,
                "subtotal_cost": subtotal_cost,
                "subtotal": subtotal,
                "margin_amount": margin,
            })

        # Chequeo de duplicados: mismo cliente + misma fecha + mismos
        # productos/cantidades ya cargados. No aplica a remitos generados
        # a partir de una orden (esos ya son únicos por order_id).
        if obj_in.order_id is None and not obj_in.force:
            self._raise_if_duplicate_sales_invoice(
                client_id=obj_in.client_id,
                invoice_date=obj_in.invoice_date,
                items_data=items_data,
            )

        _client_snapshot = (
            self._build_client_snapshot(client) if client else None
        )
        _branch_snapshot = (
            self._build_branch_snapshot(branch) if branch else None
        )
        _sales_rep_snapshot = self._build_sales_rep_snapshot(current_user)

        invoice = self.sales_invoice_repo.create(
            obj_in=obj_in,
            total_cost=total_cost,
            total_amount=total_amount,
            margin_amount=total_margin,
            items_data=items_data,
            sales_rep_id=current_user.id,
            client_snapshot=_client_snapshot,
            client_branch_snapshot=_branch_snapshot,
            sales_rep_snapshot=_sales_rep_snapshot,
        )

        return self.sales_invoice_repo.get_by_id(invoice.id)
        
    def create_from_order(self, order_id: int, current_user: SalesRep):
        order = self.order_repo.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Orden no encontrada",
            )
        if not order.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La orden no tiene items",
            )
        if order.invoice_generated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La orden ya tiene un remito generada",
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
            unit_cost     = Decimal(str(item.unit_cost))
            unit_price    = Decimal(str(item.unit_price))
            subtotal_cost = Decimal(str(item.subtotal_cost))
            subtotal      = Decimal(str(item.subtotal))
            margin_amount = Decimal(str(item.margin_amount))

            total_cost   += subtotal_cost
            total_amount += subtotal
            total_margin += margin_amount

            items_data.append({
                "product_id":       item.product_id,
                "product_name":     item.product_name_snapshot,
                "product_brand":    item.product_brand_snapshot,
                "product_sku":      item.product_sku_snapshot,
                "product_snapshot": getattr(item, "product_snapshot", None),
                "quantity":         item.quantity,
                "unit_cost":        unit_cost,
                "unit_price":       unit_price,
                "subtotal_cost":    subtotal_cost,
                "subtotal":         subtotal,
                "margin_amount":    margin_amount,
            })

        invoice_number = self.sales_invoice_repo.generate_invoice_number()

        _client_snapshot = (
            order.client_snapshot
            if isinstance(order.client_snapshot, dict)
            else self._build_client_snapshot(client) if client else None
        )
        _branch_snapshot = (
            order.client_branch_snapshot
            if isinstance(order.client_branch_snapshot, dict)
            else None
        )

        _sales_rep_snapshot: dict = self._build_sales_rep_snapshot(current_user)

        obj_in = SalesInvoiceCreate(
            order_id               = order.id,
            sales_type             = order.sales_type,
            client_id              = order.client_id,
            client_branch_id       = order.client_branch_id,
            customer_name          = order.customer_name,
            customer_phone         = order.customer_phone,
            customer_email         = order.customer_email,
            delivery_type          = order.delivery_type,
            delivery_address       = order.delivery_address,
            delivery_city          = order.delivery_city,
            delivery_reference     = order.delivery_reference,
            sales_rep_id           = order.sales_rep_id,
            invoice_number         = invoice_number,
            invoice_date           = date.today(),
            currency               = getattr(order, "currency", "ARS"),
            items=[
                SalesInvoiceItemCreate(
                    product_id    = item["product_id"],
                    product_name  = item["product_name"],
                    product_brand = item["product_brand"],
                    product_sku   = item["product_sku"],
                    quantity      = item["quantity"],
                )
                for item in items_data
            ],
        )

        invoice = self.sales_invoice_repo.create(
            obj_in                 = obj_in,
            total_cost             = total_cost,
            total_amount           = total_amount,
            margin_amount          = total_margin,
            items_data             = items_data,
            sales_rep_id           = current_user.id,
            client_snapshot        = _client_snapshot,
            client_branch_snapshot = _branch_snapshot,
            sales_rep_snapshot     = _sales_rep_snapshot,
        )

        order.invoice_generated = True
        self.db.add(order)
        self.db.flush()
        self.db.refresh(invoice)

        return invoice

    def update(self, sales_invoice_id: int, data: SalesInvoiceUpdate):
        sales_invoice = self.get_by_id(sales_invoice_id)

        if sales_invoice.status == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede editar un remito cancelado",
            )

        if data.client_branch_id is not None:
            client = self.client_repo.get_by_id(sales_invoice.client_id)
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

        if data.order_id is not None:
            order = self.order_repo.get_order_by_id(data.order_id)
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Orden asociada no encontrada",
                )

            if order.client_id != sales_invoice.client_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La orden asociada no pertenece al mismo cliente del remito",
                )

            future_branch_id = (
                data.client_branch_id
                if "client_branch_id" in data.model_dump(exclude_unset=True)
                else sales_invoice.client_branch_id
            )

            if order.client_branch_id != future_branch_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La sucursal de la orden no coincide con la del remito",
                )

        return self.sales_invoice_repo.update(sales_invoice, data)
    
    # ------------------------------------------------------------------
    # Pagos de remitos ONLINE (contra entrega — sin cuenta corriente)
    # ------------------------------------------------------------------

    def register_online_payment(
        self,
        sales_invoice_id: int,
        data: SalesInvoicePaymentCreate,
        current_user: SalesRep | None,
    ) -> SalesInvoicePaymentListResponse:
        if data.payment_method not in ALLOWED_PAYMENT_METHODS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Método de pago inválido",
            )

        invoice = self.sales_invoice_repo.get_by_id(sales_invoice_id)

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Remito de venta no encontrado",
            )

        if invoice.client_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Este remito tiene cliente con cuenta corriente — "
                    "registrá el cobro con /client-account-movements en vez de este endpoint"
                ),
            )

        if invoice.status != "confirmed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden registrar cobros sobre remitos confirmados",
            )

        total = invoice.total_amount or Decimal("0.00")
        remaining = total - invoice.paid_amount

        if data.amount > remaining:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El monto supera el saldo pendiente del remito (${remaining})",
            )

        self.sales_invoice_payment_repo.create_without_commit(
            {
                "sales_invoice_id": invoice.id,
                "amount": data.amount,
                "payment_method": data.payment_method,
                "notes": data.notes,
                "created_by": current_user.id if current_user else None,
            }
        )

        invoice.paid_amount = invoice.paid_amount + data.amount

        if invoice.paid_amount >= total and total > 0:
            invoice.payment_status = "paid"
        elif invoice.paid_amount > 0:
            invoice.payment_status = "partial"
        else:
            invoice.payment_status = "pending"

        self.db.add(invoice)

        self.db.flush()
        self.db.refresh(invoice)

        return self._build_online_payment_list_response(invoice)

    def get_online_payments(self, sales_invoice_id: int) -> SalesInvoicePaymentListResponse:
        invoice = self.sales_invoice_repo.get_by_id(sales_invoice_id)

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Remito de venta no encontrado",
            )

        return self._build_online_payment_list_response(invoice)

    def _build_online_payment_list_response(
        self, invoice: SalesInvoice
    ) -> SalesInvoicePaymentListResponse:
        payments = self.sales_invoice_payment_repo.get_by_invoice_id(invoice.id)

        return SalesInvoicePaymentListResponse(
            payments=[
                SalesInvoicePaymentResponse.model_validate(p) for p in payments
            ],
            payment_status=invoice.payment_status,
            paid_amount=invoice.paid_amount,
            total_amount=invoice.total_amount,
        )

    def _register_invoice_receivable(
        self,
        invoice: SalesInvoice,
        current_user: SalesRep | None,
    ) -> None:
        """
        Registra la deuda generada por el remito en la cuenta corriente
        del cliente.
        """
        if not invoice.total_amount:
            return

        if invoice.client_id is not None:
            self.client_account_movement_service.apply_movement(
                client_id=invoice.client_id,
                movement_type="invoice",
                amount=invoice.total_amount,
                reference_type="sales_invoice",
                reference_id=invoice.id,
                notes=f"Remito de venta #{invoice.id}",
                created_by=current_user.id if current_user else None,
            )

    def update_status(
        self,
        sales_invoice_id: int,
        status_value: str,
        current_user: SalesRep | None = None,
    ) -> SalesInvoice:
        if status_value not in ALLOWED_SALES_INVOICE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estado de remito de venta inválido",
            )

        invoice = self.get_by_id(sales_invoice_id)
        current_status = invoice.status

        if current_status == status_value:
            return invoice

        if current_status == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede cambiar el estado de un remito cancelado",
            )

        if current_status == "confirmed" and status_value != "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El remito ya está emitido y solo puede cancelarse",
            )

        if status_value == "cancelled":
            # Si ya tiene pagos imputados, no se puede cancelar sin antes
            # revertir/reasignar esos pagos manualmente (evita descuadres).
            if invoice.paid_amount and invoice.paid_amount > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "No se puede cancelar: el remito ya tiene pagos "
                        "imputados. Revertí o reasigná esos pagos primero."
                    ),
                )

            # Si estaba confirmada, reponer el stock y revertir el movimiento de cuenta corriente
            if current_status == "confirmed":
                # Si el stock lo consumió el pedido (order.stock_consumed), es el
                # pedido quien lo repone al cancelarse. Reponerlo acá también lo
                # duplicaría. Es el espejo de la confirmación, que en ese caso
                # tampoco descuenta stock desde el remito.
                order_owns_stock = False
                if invoice.order_id is not None:
                    linked_order = self.order_repo.get_order_by_id(invoice.order_id)
                    order_owns_stock = bool(linked_order and linked_order.stock_consumed)

                if not order_owns_stock:
                    for item in invoice.items:
                        self.inventory_movement_service.apply_movement(
                            product_id=item.product_id,
                            movement_type="adjustment_in",
                            quantity=item.quantity,
                            reference_type="sales_invoice",
                            reference_id=invoice.id,
                            notes=f"Reposición por cancelación de remito #{invoice.id}",
                        )

                if invoice.total_amount and invoice.client_id is not None:
                    self.client_account_movement_service.apply_movement(
                        client_id=invoice.client_id,
                        movement_type="invoice_reversal",
                        amount=invoice.total_amount,
                        reference_type="sales_invoice",
                        reference_id=invoice.id,
                        notes=f"Reversión por cancelación de remito #{invoice.id}",
                        created_by=current_user.id if current_user else None,
                    )

            result = self.sales_invoice_repo.update_status(
                sales_invoice=invoice,
                status_value=status_value,
            )
            self.db.flush()
            self.db.refresh(result)
            return result

        if status_value == "confirmed":
            if not invoice.items:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El remito no tiene items",
                )

            if invoice.order_id is not None:
                invoice_counter = Counter(
                    {item.product_id: item.quantity for item in invoice.items}
                )
                self._validate_order_link(
                    order_id=invoice.order_id,
                    client_id=invoice.client_id,
                    client_branch_id=invoice.client_branch_id,
                    invoice_items_counter=invoice_counter,
                    sales_type=SalesType(invoice.sales_type),
                    check_invoice_generated=False,
                )

                order = self.order_repo.get_order_by_id(invoice.order_id)
                if order and order.stock_consumed:
                    self._register_invoice_receivable(invoice, current_user)

                    result = self.sales_invoice_repo.update_status(
                        sales_invoice=invoice,
                        status_value=status_value,
                    )
                    self.db.flush()
                    self.db.refresh(result)
                    return result

            for item in invoice.items:
                product = self.product_repo.get_product_by_name(item.product_name)
                if not product:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Producto con id {item.product_name} no encontrado",
                    )
                if not product.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"El producto {product.name} está inactivo",
                    )

            # Descontar stock por cada ítem del remito
            for item in invoice.items:
                self.inventory_movement_service.apply_movement(
                    product_id=item.product_id,
                    movement_type="sale",
                    quantity=item.quantity,
                    reference_type="sales_invoice",
                    reference_id=invoice.id,
                    notes=f"Salida por remito de venta #{invoice.id}",
                )

            self._register_invoice_receivable(invoice, current_user)

            result = self.sales_invoice_repo.update_status(
                sales_invoice=invoice,
                status_value=status_value,
            )
            self.db.flush()
            self.db.refresh(result)
            return result

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transición de estado no permitida",
        )