from decimal import Decimal
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.constants.purchase_quote_constant import ALLOWED_PURCHASE_QUOTE_STATUSES
from app.models.purchase_quote_model import PurchaseQuote
from app.models.sales_rep_model import SalesRep
from app.repositories.product_repository import ProductRepository
from app.repositories.purchase_quote_repository import PurchaseQuoteRepository
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.purchase_quote_schema import (
    PurchaseQuoteCreate,
    PurchaseQuoteLinkProduct,
    PurchaseQuoteUpdate,
    SupplierSnapshot,
)
from app.utils.import_matching import build_items_signature, is_same_document

class PurchaseQuoteService:
    """
    Presupuestos de compra: documentos de cotización a proveedores,
    independientes de los remitos de compra. No afectan stock ni cuenta
    corriente; solo cambian de estado (draft/sent/approved/rejected/expired).
    """

    def __init__(self, db: Session):
        self.db = db
        self.purchase_quote_repo = PurchaseQuoteRepository(db)
        self.product_repo = ProductRepository(db)
        self.supplier_repo = SupplierRepository(db)

    def _get_quote_or_404(self, purchase_quote_id: int) -> PurchaseQuote:
        quote = self.purchase_quote_repo.get_by_id(purchase_quote_id)
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Presupuesto de compra no encontrado",
            )
        return quote

    def get_purchase_quotes(
        self,
        page: int = 1,
        page_size: int = 10,
        status_value: Optional[str] = None,
        supplier_id: Optional[int] = None,
    ):
        purchase_quotes, total = self.purchase_quote_repo.get_purchase_quotes(
            page=max(1, page),
            page_size=max(1, page_size),
            status=status_value,
            supplier_id=supplier_id,
        )

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return {
            "purchase_quotes": purchase_quotes,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_by_id(self, purchase_quote_id: int) -> PurchaseQuote:
        return self._get_quote_or_404(purchase_quote_id)

    def create(self, data: PurchaseQuoteCreate, current_user: Optional[SalesRep]):
        # 1. Resolución de proveedor (opcional: puede cotizarse a proveedor libre por nombre)
        supplier = None
        supplier_snapshot = None

        if data.supplier_id:
            supplier = self.supplier_repo.get_by_id(data.supplier_id)
            if not supplier:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Proveedor no encontrado",
                )
        elif data.supplier_tax_id:
            supplier = self.supplier_repo.get_by_tax_id(data.supplier_tax_id)

        if supplier and not supplier.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El proveedor está inactivo",
            )

        if supplier:
            supplier_snapshot = SupplierSnapshot(
                id=supplier.id,
                name=supplier.name,
                tax_id=supplier.tax_id,
            ).model_dump()

        supplier_id = supplier.id if supplier else None
        supplier_name = supplier.name if supplier else data.supplier_name
        supplier_tax_id = supplier.tax_id if supplier else data.supplier_tax_id

        if not supplier_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe indicarse un proveedor (supplier_id o supplier_name)",
            )

        if not data.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El presupuesto debe tener al menos un ítem.",
            )

        # 2. Preparación de ítems y cálculo de total
        items_data = []
        total_amount = Decimal("0.00")

        for item in data.items:
            unit_cost = Decimal(str(item.unit_cost))
            subtotal = (unit_cost * item.quantity)
            total_amount += subtotal

            # Vincular al producto existente por id, SKU o nombre si no
            # vino ya resuelto. No afecta stock ni costo: un presupuesto
            # es solo cotización.
            product_id = item.product_id
            if not product_id:
                matched = self.product_repo.find_by_sku_or_name(
                    item.product_sku, item.product_name
                )
                if matched:
                    product_id = matched.id

            items_data.append({
                "product_id": product_id,
                "product_name": item.product_name.strip() if item.product_name else "Producto sin nombre",
                "product_sku": item.product_sku.strip() if item.product_sku else None,
                "quantity": item.quantity,
                "unit_cost": unit_cost,
                "subtotal": subtotal,
            })

        payload = data.model_copy(update={
            "supplier_id": supplier_id,
            "supplier_name": supplier_name,
            "supplier_tax_id": supplier_tax_id,
        })

        if not data.force:
            self._raise_if_duplicate_purchase_quote(
                supplier_id=supplier_id,
                supplier_name=supplier_name,
                quote_date=data.quote_date,
                items_data=items_data,
            )

        return self.purchase_quote_repo.create(
            obj_in=payload,
            supplier_snapshot=supplier_snapshot,
            total_amount=total_amount,
            items_data=items_data,
            created_by=current_user.id if current_user else None,
        )

    def _raise_if_duplicate_purchase_quote(
        self,
        *,
        supplier_id: Optional[int],
        supplier_name: Optional[str],
        quote_date,
        items_data: list[dict],
    ) -> None:
        candidates = self.purchase_quote_repo.get_active_by_supplier_and_date(
            supplier_id=supplier_id,
            supplier_name=supplier_name,
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
                        "Ya existe un presupuesto de compra activo con el "
                        f"mismo proveedor, fecha ({quote_date}) y los mismos "
                        f"productos/cantidades (presupuesto #{existing_quote.id}). "
                        "Si de verdad es distinto, reenviá con force=true."
                    ),
                )

    def update(self, purchase_quote_id: int, data: PurchaseQuoteUpdate) -> PurchaseQuote:
        quote = self._get_quote_or_404(purchase_quote_id)
        return self.purchase_quote_repo.update(db_obj=quote, obj_in=data)

    def link_item_to_product(
        self,
        purchase_quote_id: int,
        item_id: int,
        data: PurchaseQuoteLinkProduct,
    ):
        quote = self._get_quote_or_404(purchase_quote_id)
        item = self.purchase_quote_repo.get_item_by_id(item_id)

        if not item or item.purchase_quote_id != quote.id:
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

        return self.purchase_quote_repo.link_item_to_product(item, data.product_id)

    def update_status(
        self,
        purchase_quote_id: int,
        status_value: str,
        current_user: Optional[SalesRep] = None,
    ) -> PurchaseQuote:
        quote = self._get_quote_or_404(purchase_quote_id)
        status_value = status_value.lower()

        if status_value not in ALLOWED_PURCHASE_QUOTE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estado inválido. Valores permitidos: {sorted(ALLOWED_PURCHASE_QUOTE_STATUSES)}",
            )

        return self.purchase_quote_repo.update_status(quote, status_value)