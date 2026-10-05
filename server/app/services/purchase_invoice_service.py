from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.purchase_invoice_model import PurchaseInvoice
from app.models.product_model import Product
from app.models.sales_rep_model import SalesRep
from app.services.inventory_movement_service import InventoryMovementService
from app.services.product_service import ProductService
from app.services.supplier_account_movement_service import SupplierAccountMovementService
from app.repositories.inventory_movement_repository import InventoryMovementRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.purchase_invoice_repository import PurchaseInvoiceRepository
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.product_schema import ProductCreateDraft
from app.schemas.purchase_invoice_schema import (
    PurchaseInvoiceCreate,
    PurchaseInvoiceLinkProduct,
    PurchaseInvoiceUpdate,
    SupplierSnapshot,
)
from app.utils.slug import slugify
from app.utils.import_matching import build_items_signature, is_same_document

_UNSET = object()

class PurchaseInvoiceService:
    def __init__(self, db: Session):
        self.db = db
        self.purchase_invoice_repo = PurchaseInvoiceRepository(db)
        self.product_repo = ProductRepository(db)
        self.supplier_repo = SupplierRepository(db)
        self.inventory_movement_repo = InventoryMovementRepository(db)
        self.inventory_movement_service = InventoryMovementService(db)
        self.supplier_account_movement_service = SupplierAccountMovementService(db)
        self.product_service = ProductService(db)

    def _get_invoice_or_404(self, purchase_invoice_id: int):
        invoice = self.purchase_invoice_repo.get_by_id(purchase_invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Remito de compra no encontrada"
            )
        return invoice

    def get_purchase_invoices(
        self,
        page: int = 1,
        page_size: int = 10,
        status_value: Optional[str] = None,
    ):
        # Las validaciones de page > 1 suelen manejarse en el Schema (Query params), 
        # pero las mantenemos por seguridad.
        purchase_invoices, total = self.purchase_invoice_repo.get_purchase_invoices(
            page=max(1, page),
            page_size=max(1, page_size),
            status=status_value,
        )

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return {
            "purchase_invoices": purchase_invoices,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
        
    def get_by_id(
        self,
        purchase_invoice_id: int,
    ) -> PurchaseInvoice:
        return self._get_invoice_or_404(purchase_invoice_id)

    def create(self, data: PurchaseInvoiceCreate, current_user: Optional[SalesRep]):
        # 1. Resolución de Proveedor
        supplier = None
        supplier_snapshot = None
        
        if data.supplier_id:
            supplier = self.supplier_repo.get_by_id(data.supplier_id)

            if not supplier:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Proveedor no encontrado"
                )
        elif data.supplier_tax_id:
            supplier = self.supplier_repo.get_by_tax_id(data.supplier_tax_id)
            
            if not supplier:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Proveedor no encontrado por tax_id"
                )
            
        if supplier and not supplier.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El proveedor está inactivo"
            )
            
        if supplier:
            supplier_snapshot = SupplierSnapshot(
                id=supplier.id,
                name=supplier.name,
                tax_id=supplier.tax_id
            ).model_dump()
            
        
        supplier_id = supplier.id if supplier else None
        supplier_name = supplier.name if supplier else data.supplier_name
        supplier_tax_id = supplier.tax_id if supplier else data.supplier_tax_id

        if not data.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El remito debe tener al menos un item."
            )

        # 2. Preparación de Items y Cálculo de Total
        items_data = []
        total_amount = Decimal("0.00")

        for item in data.items:
            subtotal = Decimal(str(item.unit_cost)) * item.quantity
            total_amount += subtotal
            items_data.append({
                "product_id": item.product_id,
                "product_name": item.product_name.strip() if item.product_name else "Producto sin nombre",
                "product_sku": item.product_sku.strip() if item.product_sku else None,
                "quantity": item.quantity,
                "unit_cost": Decimal(str(item.unit_cost)),
                "subtotal": subtotal,
            })

        # 2.5. Chequeo de duplicados: mismo proveedor + misma fecha +
        # mismos productos/cantidades ya cargados (típico de reimportar el
        # mismo PDF/Excel dos veces).
        if not data.force:
            self._raise_if_duplicate_purchase_invoice(
                supplier_id=supplier_id,
                supplier_name=supplier_name,
                invoice_date=data.invoice_date,
                items_data=items_data,
            )

        # 3. Persistencia
        payload = data.model_copy(update={
            "supplier_id": supplier_id,
            "supplier_name": supplier_name,
            "supplier_tax_id": supplier_tax_id
        })

        return self.purchase_invoice_repo.create(
            obj_in=payload,
            supplier_snapshot=supplier_snapshot,
            total_amount=total_amount,
            items_data=items_data,
            created_by=current_user.id if current_user else None
        )

    def _raise_if_duplicate_purchase_invoice(
        self,
        *,
        supplier_id: Optional[int],
        supplier_name: Optional[str],
        invoice_date,
        items_data: list[dict],
    ) -> None:
        candidates = self.purchase_invoice_repo.get_active_by_supplier_and_date(
            supplier_id=supplier_id,
            supplier_name=supplier_name,
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
                        "Ya existe un remito de compra activo con el mismo "
                        f"proveedor, fecha ({invoice_date}) y los mismos "
                        f"productos/cantidades (remito #{existing_invoice.id}, "
                        f"'{existing_invoice.invoice_number}'). Si de verdad "
                        "es un remito distinto, reenviá con force=true."
                    ),
                )

    def _calculate_weighted_average_cost(
        self,
        current_stock: int,
        current_cost: Decimal,
        incoming_qty: int,
        incoming_cost: Decimal,
    ) -> Decimal:
        """Costo Promedio Ponderado (CPP)."""
        new_stock = current_stock + incoming_qty
        
        if new_stock <= 0 or current_stock <= 0:
            return incoming_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total_value = (Decimal(current_stock) * current_cost) + (Decimal(incoming_qty) * incoming_cost)
        weighted_cost = total_value / Decimal(new_stock)
        
        return weighted_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _resolve_product_for_item(self, item) -> Product:
        """Busca el producto por ID, SKU o crea uno nuevo si es necesario."""
        if item.product_id:
            product = self.product_repo.get_product_by_id(item.product_id)
            if product: return product

        if item.product_sku:
            product = self.product_repo.get_product_by_sku(item.product_sku.strip())
            if product:
                item.product_id = product.id
                return product

        # Crear producto genérico si no existe
        base_slug = slugify(item.product_name or "nuevo-producto")
        unique_slug = self.product_repo.get_unique_slug(base_slug)
        
        new_product_data = ProductCreateDraft(
            sku=item.product_sku.strip() if item.product_sku else None,
            name=item.product_name.strip(),
            unit_cost=item.unit_cost,
            unit_price=item.unit_cost * Decimal("1.3"), # Margen estimado del 30%
            slug=unique_slug
        )
        product = self.product_repo.create_without_commit(new_product_data)
        self.db.flush() # Para obtener el ID
        item.product_id = product.id
        return product

    def _register_invoice_payable(
        self,
        invoice: PurchaseInvoice,
        current_user: Optional[SalesRep],
    ) -> None:
        """
        Registra en la cuenta corriente del proveedor lo que le pasamos a deber
        por este remito. Solo aplica si hay un proveedor asociado (registrado
        con id, no solo un nombre libre).
        """
        if invoice.supplier_id is None or not invoice.total_amount:
            return

        self.supplier_account_movement_service.apply_movement(
            supplier_id=invoice.supplier_id,
            movement_type="invoice",
            amount=invoice.total_amount,
            reference_type="purchase_invoice",
            reference_id=invoice.id,
            notes=f"Remito de compra #{invoice.id}",
            created_by=current_user.id if current_user else None,
        )

    def update(
        self,
        purchase_invoice_id: int,
        data: PurchaseInvoiceUpdate,
    ) -> PurchaseInvoice:
        invoice = self._get_invoice_or_404(purchase_invoice_id)

        if invoice.status == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede editar un remito cancelado",
            )

        update_data = data.model_dump(exclude_unset=True)
        new_snapshot: dict | None | object = _UNSET  # sentinel: no tocar el snapshot

        # Si se está reasignando el proveedor, re-resolvemos y refrescamos
        # el snapshot para que quede consistente con los datos actuales.
        if "supplier_id" in update_data:
            if data.supplier_id is None:
                new_snapshot = None
                if not update_data.get("supplier_name") and not invoice.supplier_name:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Debe indicarse un proveedor (supplier_id o supplier_name)",
                    )
            else:
                supplier = self.supplier_repo.get_by_id(data.supplier_id)
                if not supplier:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Proveedor no encontrado",
                    )
                if not supplier.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="El proveedor está inactivo",
                    )

                update_data["supplier_name"] = update_data.get("supplier_name") or supplier.name
                update_data["supplier_tax_id"] = update_data.get("supplier_tax_id") or supplier.tax_id
                new_snapshot = SupplierSnapshot(
                    id=supplier.id,
                    name=supplier.name,
                    tax_id=supplier.tax_id,
                ).model_dump()

        payload = PurchaseInvoiceUpdate(**update_data)
        updated_invoice = self.purchase_invoice_repo.update(db_obj=invoice, obj_in=payload)

        if new_snapshot is not _UNSET:
            updated_invoice.supplier_snapshot = new_snapshot
            self.db.flush()
            self.db.refresh(updated_invoice)

        return updated_invoice

    def link_item_to_product(
        self,
        purchase_invoice_id: int,
        item_id: int,
        data: PurchaseInvoiceLinkProduct,
    ):
        invoice = self._get_invoice_or_404(purchase_invoice_id)
        item = self.purchase_invoice_repo.get_item_by_id(item_id)

        if not item or item.purchase_invoice_id != invoice.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ítem no encontrado en este remito",
            )

        product = self.product_repo.get_product_by_id(data.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado",
            )

        return self.purchase_invoice_repo.link_item_to_product(item, data.product_id)

    def update_status(
        self,
        purchase_invoice_id: int,
        status_value: str,
        current_user: Optional[SalesRep] = None,
    ):

        invoice = self._get_invoice_or_404(
            purchase_invoice_id
        )

        status_value = status_value.lower()

        if (
            status_value == "confirmed"
            and invoice.status != "confirmed"
        ):

            # =========================
            # 1. Vincular productos
            # =========================

            for item in invoice.items:
                if not item.product_id:
                    existing_p = (
                        self.product_repo.find_by_sku_or_name(
                            item.product_sku,
                            item.product_name,
                        )
                    )

                    if existing_p:
                        item.product_id = existing_p.id

                    else:
                        base_slug = slugify(
                            item.product_name
                        )

                        unique_slug = (
                            self.product_repo.get_unique_slug(
                                base_slug
                            )
                        )

                        new_product = (
                            self.product_repo.create_product_no_commit(
                                ProductCreateDraft(
                                    name=item.product_name,
                                    description=(
                                        "Creado automáticamente "
                                        "desde remito de compra."
                                    ),
                                    slug=unique_slug,
                                    unit_cost=item.unit_cost,
                                    unit_price=(
                                        item.unit_cost
                                        * Decimal("1.3")
                                    ),
                                    currency="ARS",
                                    stock_current=0,
                                    stock_min=0,
                                    sku=item.product_sku,
                                    image_url=None,
                                    is_active=False,
                                )
                            )
                        )

                        # El producto permanece inactivo en estado DRAFT
                        # hasta que sea completado y activado manualmente
                        new_product.status = "DRAFT"
                        new_product.is_active = False

                        self.db.flush()

                        item.product_id = new_product.id

            # =========================
            # 2. Lock productos
            # =========================

            product_ids = [
                it.product_id
                for it in invoice.items
            ]

            products_db = (
                self.product_repo
                .get_products_by_ids_for_update(
                    product_ids
                )
            )

            products_map = {
                p.id: p
                for p in products_db
            }

            # =========================
            # 3. Actualizar stock/costos
            # =========================

            for item in invoice.items:

                product = products_map.get(
                    item.product_id
                )

                if not product:
                    continue

                incoming_qty = item.quantity
                incoming_cost = item.unit_cost

                self.product_service.apply_weighted_average_cost(
                    product,
                    incoming_qty,
                    incoming_cost,
                )

                self.inventory_movement_service.apply_movement(
                    product_id=item.product_id,
                    movement_type="purchase",
                    quantity=incoming_qty,
                    reference_type="purchase_invoice",
                    reference_id=invoice.id,
                )

                # Historial de compras del producto: costo y cantidad de este remito.
                self.product_service.purchase_history.record(
                    product_id=item.product_id,
                    quantity=incoming_qty,
                    unit_cost=incoming_cost,
                    source="purchase_invoice",
                    reference_id=invoice.id,
                    created_by=getattr(current_user, "id", None),
                )

            # =========================
            # 4. Cuenta corriente del proveedor
            # =========================

            self._register_invoice_payable(invoice, current_user)

            # =========================
            # 5. Actualizar estado
            # =========================

            self.purchase_invoice_repo.update_status(
                invoice,
                status_value,
            )

            return invoice

        # =========================
        # Otros estados
        # =========================

        # Si se cancela un remito ya confirmado, revertimos su movimiento
        # de cuenta corriente (el stock/costo no se revierte automáticamente
        # hoy — si tu operación lo necesita, hay que sumarlo aparte).
        if status_value == "cancelled":
            if invoice.paid_amount and invoice.paid_amount > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "No se puede cancelar: el remito ya tiene pagos "
                        "imputados. Revertí o reasigná esos pagos primero."
                    ),
                )

            if invoice.status == "confirmed" and invoice.supplier_id is not None and invoice.total_amount:
                self.supplier_account_movement_service.apply_movement(
                    supplier_id=invoice.supplier_id,
                    movement_type="invoice_reversal",
                    amount=invoice.total_amount,
                    reference_type="purchase_invoice",
                    reference_id=invoice.id,
                    notes=f"Reversión por cancelación de remito de compra #{invoice.id}",
                    created_by=current_user.id if current_user else None,
                )

        updated_invoice = (
            self.purchase_invoice_repo.update_status(
                invoice,
                status_value,
            )
        )

        self.db.flush()

        return updated_invoice