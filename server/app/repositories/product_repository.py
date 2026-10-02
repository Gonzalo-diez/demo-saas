from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from decimal import Decimal
from app.db.errors import handle_product_integrity_error
from app.models.product_model import Product
from app.schemas.product_schema import ProductCreateAdmin, ProductCreateDraft, ProductUpdate
from app.utils.normalize_text import normalize_text
from app.utils.slug import slugify
from app.utils.category_normalizer import get_all_canonical_categories

class ProductRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def _normalize_update_data(self, data: dict) -> dict:
        normalized = data.copy()

        if "name" in normalized:
            normalized["name_normalized"] = normalize_text(normalized["name"])

        if "brand" in normalized:
            normalized["brand_normalized"] = normalize_text(normalized["brand"])

        if "category" in normalized:
            normalized["category_normalized"] = normalize_text(normalized["category"])

        return normalized
        
    def _prepare_data(self, data: dict) -> dict:
        # Aseguramos que existan valores para las columnas NOT NULL
        if not data.get("brand"): data["brand"] = "Pendiente"
        if not data.get("category"): data["category"] = "Sin Clasificar"
        
        # Normalización
        data["name_normalized"] = normalize_text(data.get("name") or "")
        data["brand_normalized"] = normalize_text(data["brand"])
        data["category_normalized"] = normalize_text(data["category"])
        
        return data

    def get_products(
        self,
        search: str | None = None,
        brand: str | None = None,
        category: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 20,
        sort: str | None = None,
        catalog_only: bool = False,
    ):
        query = select(Product)

        if is_active is not None:
            query = query.where(Product.is_active == is_active)

        if catalog_only:
            # El catálogo online (visto por un Client) solo puede mostrar
            # categorías "seteadas"; las categorías libres/internas son
            # para venta B2B y nunca deben llegar a este listado.
            query = query.where(Product.category_normalized.in_(get_all_canonical_categories()))

        if search:
            search_term = f"%{search.strip()}%"
            query = query.where(
                Product.name.ilike(search_term)
                | Product.brand.ilike(search_term)
                | Product.category.ilike(search_term)
                | Product.sku.ilike(search_term)
            )

        if brand:
            query = query.where(Product.brand == brand)

        if category:
            query = query.where(Product.category == category)

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query) or 0

        if sort == "name-asc":
            query = query.order_by(Product.name.asc())
        elif sort == "name-desc":
            query = query.order_by(Product.name.desc())
        elif sort == "price-asc":
            query = query.order_by(Product.unit_price.asc())
        elif sort == "price-desc":
            query = query.order_by(Product.unit_price.desc())
        else:
            query = query.order_by(Product.id.desc())

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        products = self.db.scalars(query).all()
        return products, total
    
    def get_product_by_name(self, product_name: str):
        normalized_product_name = product_name.strip()
        
        query = select(Product).where(Product.name.ilike(normalized_product_name))
        return self.db.scalar(query)

    def get_product_by_id(self, product_id: int):
        query = select(Product).where(Product.id == product_id)
        return self.db.scalar(query)

    def get_product_by_sku(self, sku: str):
        if not sku:
            return None

        normalized_sku = sku.strip()
        stmt = select(Product).where(Product.sku == normalized_sku)
        return self.db.scalar(stmt)
    
    def find_by_sku_or_name(self, sku: str | None, name: str | None) -> Product | None:
        """
        Busca un producto existente primero por SKU exacto y, si no hay
        SKU o no matchea, por nombre (normalizado/ilike). Es el criterio
        canónico de "¿este producto ya existe?" para todos los flujos de
        importación (Excel de productos, remitos, presupuestos, ledger).
        """
        if sku:
            product = self.get_product_by_sku(sku)
            if product:
                return product

        if name:
            return self.get_product_by_name(name)

        return None

    def get_products_by_skus(self, skus: list[str]) -> list[Product]:
        normalized_skus = [sku.strip() for sku in skus if sku and sku.strip()]
        if not normalized_skus:
            return []

        stmt = select(Product).where(Product.sku.in_(normalized_skus))
        return list(self.db.scalars(stmt).all())

    def get_product_by_identity(
        self,
        name: str,
        brand: str,
        category: str,
    ):
        normalized_name = normalize_text(name)
        normalized_brand = normalize_text(brand)
        normalized_category = normalize_text(category)

        query = select(Product).where(
            Product.name_normalized == normalized_name,
            Product.brand_normalized == normalized_brand,
            Product.category_normalized == normalized_category,
        )
        return self.db.scalar(query)
    
    def get_products_by_ids(self, ids: list[int]) -> list[Product]:
        """Obtiene una lista de productos por sus IDs en una sola consulta."""
        query = select(Product).where(Product.id.in_(ids))
        return list(self.db.scalars(query).all())

    def get_products_by_ids_for_update(self, ids: list[int]) -> list[Product]:
        """
        Obtiene los productos y bloquea las filas (SELECT FOR UPDATE).
        Esencial para procesos que modifican stock.
        """
        query = (
            select(Product)
            .where(Product.id.in_(ids))
            .with_for_update() # Bloquea las filas hasta que termine el commit/rollback
        )
        return list(self.db.scalars(query).all())

    def create_product_no_commit(self, product_in: ProductCreateAdmin | ProductCreateDraft) -> Product:
        # Convertimos el schema a dict y aplicamos normalización
        data = self._prepare_data(product_in.model_dump())
        
        # Manejo automático de Slug si no viene
        if not data.get("slug"):
            from app.utils.slug import slugify
            base_slug = slugify(data["name"])
            data["slug"] = self.get_unique_slug(base_slug)

        product = Product(**data)
        self.db.add(product)
        try:
            self.db.flush()
        except IntegrityError as exc:
            handle_product_integrity_error(self.db, exc)
        return product
    
    def create_without_commit(self, data: ProductCreateDraft) -> Product:
        prepared_data = self._prepare_data(data.model_dump())

        product = Product(**prepared_data)

        self.db.add(product)
        self.db.flush()

        return product

    def create_product(self, product_in: ProductCreateAdmin):
        product = self.create_product_no_commit(product_in)

        self.db.add(product)
        self.db.flush()
        self.db.refresh(product)

        return product
    
    def create_without_commit_from_invoice(self, name: str, sku: str, cost: Decimal) -> Product:
        # Creamos un dict con lo mínimo
        safe_name = name.strip() if name else "Producto sin nombre"
        product_dict = {
            "name": safe_name,
            "sku": sku,
            "unit_cost": cost,
            "unit_price": cost * Decimal("1.3"), # Margen estimado
            "status": "DRAFT",
            "is_active": False # Importante: No se vende hasta que se complete
        }
        
        prepared_data = self._prepare_data(product_dict)
        
        # Generar slug único
        prepared_data["slug"] = self.get_unique_slug(slugify(safe_name))
        
        db_obj = Product(**prepared_data)
        self.db.add(db_obj)
        self.db.flush() 
        return db_obj

    def update_product_no_commit(self, product: Product, product_in: ProductUpdate) -> Product:
        update_data = product_in.model_dump(
            exclude_unset=True,
            exclude_none=True,
            exclude={"sku"}
        )

        prepared_data = self._normalize_update_data(update_data)

        for field, value in prepared_data.items():
            setattr(product, field, value)

        try:
            self.db.flush()
        except IntegrityError as exc:
            handle_product_integrity_error(self.db, exc)

        return product


    def update_product(self, product: Product, product_in: ProductUpdate):
        product = self.update_product_no_commit(product, product_in)

        self.db.flush()
        self.db.refresh(product)

        return product

    def get_product_filters(self, catalog_only: bool = False):
        brands_query = select(Product.brand).where(Product.is_active == True)
        categories_query = select(Product.category).where(Product.is_active == True)

        if catalog_only:
            brands_query = brands_query.where(Product.category_normalized.in_(get_all_canonical_categories()))
            categories_query = categories_query.where(Product.category_normalized.in_(get_all_canonical_categories()))

        brands = self.db.scalars(
            brands_query.distinct().order_by(Product.brand)
        ).all()

        categories = self.db.scalars(
            categories_query.distinct().order_by(Product.category)
        ).all()

        return {
            "brands": brands,
            "categories": categories,
        }

    def get_free_categories(self) -> list[str]:
        """
        Categorías libres (fuera de la whitelist de catálogo) en uso, sin
        duplicados por normalización. Incluye productos inactivos, porque
        la categoría sigue siendo válida para reutilizar.
        """
        query = (
            select(func.min(Product.category))
            .where(Product.category_normalized.not_in(get_all_canonical_categories()))
            .where(Product.category.is_not(None))
            .group_by(Product.category_normalized)
        )
        categories = self.db.scalars(query).all()
        return sorted((c for c in categories if c and c.strip()), key=str.casefold)

    def bulk_create_products(self, products: list[dict]):
        normalized_products = [Product(**self._prepare_data(product_data)) for product_data in products]

        self.db.add_all(normalized_products)

        try:
            self.db.flush()
        except IntegrityError as exc:
            handle_product_integrity_error(self.db, exc)

        return normalized_products

    def get_product_by_slug(self, slug: str):
        query = select(Product).where(Product.slug == slug)
        return self.db.scalar(query)


    def get_unique_slug(self, base_slug: str, current_product_id: int | None = None) -> str:
        slug = base_slug
        counter = 2

        while True:
            existing = self.get_product_by_slug(slug)

            if not existing:
                return slug

            if current_product_id is not None and existing.id == current_product_id:
                return slug

            slug = f"{base_slug}-{counter}"
            counter += 1