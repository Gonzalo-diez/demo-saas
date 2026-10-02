from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from decimal import Decimal
from app.utils.slug import slugify
from app.models.product_model import Product
from app.repositories.product_repository import ProductRepository
from app.schemas.product_schema import (
    ProductCreateAdmin,
    ProductCreateDraft,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ProductFiltersResponse,
    ProductCategoriesResponse,
)
from app.schemas.product_import_schema import ProductImportRow
from app.repositories.inventory_movement_repository import InventoryMovementRepository
from app.services.inventory_movement_service import InventoryMovementService
from app.services.notification_alert_service import NotificationAlertService
from app.utils.category_normalizer import (
    is_catalog_category,
    get_catalog_category_options,
    get_catalog_category_aliases,
)

class ProductService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProductRepository(db)
        self.inventory_movement_repo = InventoryMovementRepository(db)
        self.inventory_movement_service = InventoryMovementService(db)
        
    def _sync_stock_alert(self, product: Product) -> None:
        """Recalcula el aviso de stock del producto (bajo / cerca del mínimo / sin stock)."""
        NotificationAlertService(self.db).safe_sync_product_stock(product)

    @staticmethod
    def _has_valid_image(image_url: str | None) -> bool:
        if not image_url:
            return False

        value = image_url.strip().lower()

        return value not in {
            "nan",
            "none",
            "null",
            "n/a",
            "-"
        }
        
    def _is_product_complete(self, data: dict) -> bool:
        name = (data.get("name") or "").strip()

        brand = (data.get("brand") or "").strip().lower()

        category_raw = data.get("category")
        category = (category_raw or "").strip().lower()

        has_image = self._has_valid_image(data.get("image_url"))

        has_required_fields = all([
            name,
            brand,
            category,
        ])

        invalid_brands = ["pendiente", "sin marca"]
        invalid_categories = ["sin clasificar"]

        if not has_required_fields:
            return False

        if brand in invalid_brands or category in invalid_categories:
            return False

        if is_catalog_category(category_raw):
            # Categoría "seteada" de catálogo: exige imagen, porque este
            # producto va a mostrarse en la tienda online.
            return has_image

        # Categoría libre/interna: no va al catálogo, así que no exige
        # imagen. Puede quedar completo/activo igual para venta B2B.
        return True

    def _determine_product_state_import(self, data: dict) -> tuple[bool, str]:
        category_raw = data.get("category")
        category = (category_raw or "").strip().lower()

        is_uncategorized = category in ["sin clasificar", ""]

        if is_uncategorized:
            return False, "DRAFT"

        if is_catalog_category(category_raw):
            has_image = self._has_valid_image(data.get("image_url"))
            is_active = has_image
        else:
            # Categoría libre/interna: no exige imagen, se importa activo
            # (disponible para venta B2B) directamente.
            is_active = True

        status = "ACTIVE" if is_active else "DRAFT"

        return is_active, status

    def _get_product_or_404(self, product_id: int) -> Product:
        """Helper interno para validar existencia."""
        product = self.repo.get_product_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {product_id} no encontrado"
            )
        return product

    def list_products(
        self,
        search: Optional[str] = None,
        brand: Optional[str] = None,
        category: Optional[str] = None,
        is_active: bool = True,
        page: int = 1,
        page_size: int = 20,
        sort: Optional[str] = None,
        catalog_only: bool = False,
    ) -> ProductListResponse:
        """
        Lista productos con filtros aplicados.
        """
        products, total = self.repo.get_products(
            search=search,
            brand=brand,
            category=category,
            is_active=is_active,
            page=page,
            page_size=page_size,
            sort=sort,
            catalog_only=catalog_only,
        )

        return ProductListResponse(
            items=[ProductResponse.model_validate(p) for p in products],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_product(self, product_id: int) -> Product:
        """Retorna un producto o 404."""
        return self._get_product_or_404(product_id)
    
    def get_or_create_by_sku(
        self,
        sku: str,
        name: str,
        unit_cost: Decimal
    ) -> Product:

        product = self.repo.get_product_by_sku(sku)

        if not product:

            obj_in = ProductCreateDraft(
                sku=sku,
                name=name,
                unit_cost=unit_cost,
                unit_price=unit_cost * Decimal("1.2"),
                is_active=False
            )

            product = self.repo.create_product(obj_in=obj_in)

            product.status = "DRAFT"

        else:

            if product.unit_cost != unit_cost:
                product.unit_cost = unit_cost

        return product

    def create_product(
        self,
        *,
        product_in: ProductCreateAdmin
    ) -> Product:

        if product_in.sku:

            existing = self.repo.get_product_by_sku(product_in.sku)

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El SKU '{product_in.sku}' ya está registrado."
                )

        base_slug = product_in.slug or slugify(product_in.name)

        unique_slug = self.repo.get_unique_slug(base_slug)

        data = product_in.model_dump()

        initial_stock = Decimal(str(data.get("stock_current") or 0))

        data["stock_current"] = 0

        data["slug"] = unique_slug
        data["is_active"] = True

        product_data = ProductCreateAdmin(**data)

        is_complete = self._is_product_complete(data)

        if not is_complete:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "No se puede crear un producto incompleto. "
                    "Asegúrate de completar todos los campos requeridos."
                )
            )

        product = self.repo.create_product(
            product_in=product_data
        )

        product.status = "ACTIVE"

        if initial_stock > 0:

            self.inventory_movement_service.apply_movement(
                product_id=product.id,
                movement_type="initial_stock",
                quantity=initial_stock,
                reference_type="manual_adjustment",
                notes=f"Stock inicial producto {product.name}",
            )

        self._sync_stock_alert(product)

        return product
    
    def create_draft_product(
        self,
        *,
        product_in: ProductCreateDraft
    ) -> Product:

        if product_in.sku:
            existing = self.repo.get_product_by_sku(product_in.sku)

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El SKU '{product_in.sku}' ya existe."
                )

        base_slug = product_in.slug or slugify(product_in.name)
        unique_slug = self.repo.get_unique_slug(base_slug)
        data = product_in.model_dump()
        data["slug"] = unique_slug
        data["is_active"] = False
        draft_product = ProductCreateDraft(**data)
        product = self.repo.create_product(product_in=draft_product)
        self.repo.db.flush()
        product.status = "DRAFT"
        
        if product.stock_current > 0:
            self.inventory_movement_repo.create_without_commit({
                "product_id": product.id,
                "movement_type": "initial_stock",
                "quantity": product.stock_current,
                "stock_before": 0,
                "stock_after": product.stock_current,
                "unit_cost": product.unit_cost,
                "unit_price": product.unit_price,
                "reference_type": "draft",
                "reference_id": None,
                "notes": f"Stock inicial draft {product.name}",
                "created_by": None,
            })

        self.repo.db.flush()
        self.repo.db.refresh(product)

        return product
        
    def apply_weighted_average_cost(
        self,
        product: Product,
        incoming_qty: int,
        incoming_cost: Decimal,
    ) -> Decimal:
        """
        Costo Promedio Ponderado (CPP), centralizado para que todo lugar
        que ingresa stock de compra (import de productos, remitos de
        compra, ledger) calcule el costo de la misma forma.

        No hace commit ni genera movimiento de stock: eso queda a cargo
        del caller (que ya sabe qué reference_type/reference_id usar).
        """
        stock_before = Decimal(product.stock_current or 0)
        incoming_qty_dec = Decimal(incoming_qty)
        stock_after = stock_before + incoming_qty_dec

        if stock_after > 0 and incoming_qty_dec > 0:
            weighted_cost = (
                (stock_before * Decimal(str(product.unit_cost or 0)))
                + (incoming_qty_dec * Decimal(str(incoming_cost)))
            ) / stock_after
            product.unit_cost = weighted_cost.quantize(Decimal("0.01"))

        return product.unit_cost

    def import_products_bulk(
        self,
        rows: list[ProductImportRow],
        mode: str = "upsert",
    ) -> dict:
        """
        Procesa una lista de filas validadas del Excel de importación.
        Retorna contadores {"created": N, "updated": M} para que el caller
        pueda construir el ProductImportCommitResponse.
        """
        created_count = 0
        updated_count = 0

        for row in rows:
            # Match por SKU o, si no hay SKU o no matchea, por nombre:
            # así una fila que trae un producto ya cargado (con otro SKU
            # o sin SKU) no genera un duplicado, sino que suma stock y
            # pondera costo sobre el existente.
            existing = self.repo.find_by_sku_or_name(row.sku, row.name)

            if existing:
                incoming_stock = row.stock_current or 0
                incoming_cost  = row.unit_cost

                # Costo Promedio Ponderado si entra nuevo stock
                if incoming_stock > 0:
                    self.apply_weighted_average_cost(existing, incoming_stock, incoming_cost)

                    self.inventory_movement_service.apply_movement(
                        product_id=existing.id,
                        movement_type="adjustment_in",
                        quantity=incoming_stock,
                        reference_type="import",
                        notes="Ingreso por importación Excel",
                    )

                # Actualizar campos del producto (sin tocar stock ni costo directamente)
                update_data = row.model_dump(exclude_unset=True, exclude={"is_active"})
                update_data.pop("stock_current", None)
                update_data.pop("unit_cost", None)

                self.repo.update_product_no_commit(
                    existing,
                    ProductUpdate(**update_data),
                )
                self._sync_stock_alert(existing)
                updated_count += 1

            else:
                data = row.model_dump(exclude={"is_active"})
                is_active, product_status = self._determine_product_state_import(data)
                data["is_active"] = is_active

                new_prod = ProductCreateDraft(**data)
                prod_db  = self.repo.create_product_no_commit(new_prod)
                prod_db.status = product_status

                if prod_db.stock_current > 0:
                    self.inventory_movement_service.apply_movement(
                        product_id=prod_db.id,
                        movement_type="initial_stock",
                        quantity=prod_db.stock_current,
                        reference_type="import",
                        notes="Stock inicial por importación Excel",
                    )

                self._sync_stock_alert(prod_db)
                created_count += 1

        return {"created": created_count, "updated": updated_count}

    def update_product(self, *, product_id: int, obj_in: ProductUpdate) -> Product:
        db_obj = self._get_product_or_404(product_id)

        update_data = obj_in.model_dump(exclude_unset=True)

        # Validaciones (OK usar dict acá)
        if "name" in update_data and "slug" not in update_data:
            if update_data["name"] != db_obj.name:
                base_slug = slugify(update_data["name"])
                update_data["slug"] = self.repo.get_unique_slug(
                    base_slug,
                    current_product_id=product_id  # ⚠️ ojo acá, no exclude_id
                )

        # Merge entre estado actual + update
        current_data = {
            "name": update_data.get("name", db_obj.name),
            "brand": update_data.get("brand", db_obj.brand),
            "category": update_data.get("category", db_obj.category),
            "image_url": update_data.get("image_url", db_obj.image_url),
        }

        is_complete = self._is_product_complete(current_data)

        update_data["is_active"] = is_complete
        update_data["status"] = "ACTIVE" if is_complete else "DRAFT"

        # 🔥 RECONSTRUIR schema
        obj_in = ProductUpdate(**update_data)

        product = self.repo.update_product(product=db_obj, product_in=obj_in)
        self._sync_stock_alert(product)
        return product

    def validate_stock_availability(self, product_id: int, requested_quantity: int) -> Product:
        """
        Verifica si hay suficiente stock y si el producto está activo para la venta.
        """
        product = self._get_product_or_404(product_id)
        
        if not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El producto '{product.name}' está inactivo."
            )

        if product.stock_current < requested_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Stock insuficiente para '{product.name}'. "
                    f"Solicitado: {requested_quantity}, Disponible: {product.stock_current}"
                )
            )
        
        return product

    def get_product_filters(self, catalog_only: bool = False) -> ProductFiltersResponse:
        """
        Retorna las opciones disponibles de marcas y categorías.
        """
        filters = self.repo.get_product_filters(catalog_only=catalog_only)
        return ProductFiltersResponse(**filters)

    def get_category_options(self) -> ProductCategoriesResponse:
        """
        Opciones para el selector de categoría del admin: las de catálogo
        (visibles online) y las libres ya existentes (solo B2B).
        """
        return ProductCategoriesResponse(
            catalog=get_catalog_category_options(),
            free=self.repo.get_free_categories(),
            catalog_aliases=get_catalog_category_aliases(),
        )

    def deactivate_product(self, product_id: int) -> Product:
        db_obj = self._get_product_or_404(product_id)

        if not db_obj.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El producto ya se encuentra inactivo."
            )

        db_obj.is_active = False
        db_obj.status = "INACTIVE"

        self._sync_stock_alert(db_obj)

        return db_obj
    
    def reactivate_product(self, product_id: int) -> Product:
        db_obj = self._get_product_or_404(product_id)

        if db_obj.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El producto ya se encuentra activo."
            )

        is_complete = self._is_product_complete({
            "name": db_obj.name,
            "brand": db_obj.brand,
            "category": db_obj.category,
            "image_url": db_obj.image_url,
        })

        if not is_complete:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El producto todavía está incompleto."
            )

        db_obj.is_active = True
        db_obj.status = "ACTIVE"

        self._sync_stock_alert(db_obj)

        return db_obj