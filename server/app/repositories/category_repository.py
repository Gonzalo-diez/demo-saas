from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.category_model import Category
from app.models.product_model import Product
from app.utils.normalize_text import normalize_text
from app.utils.slug import slugify

NO_CATEGORY_LABEL = "Sin Clasificar"
PLACEHOLDER_NAMES = {"sin clasificar"}


def normalize_category_name(name: str) -> str:
    return normalize_text(" ".join(name.split())) or ""


class CategoryRepository:
    """
    Todo acá queda automáticamente acotado al tenant de la sesión
    (ver app/db/tenant_context.py): no hay que filtrar por tenant_id.
    """

    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------------- GET

    def get_by_id(self, category_id: int) -> Category | None:
        return self.db.scalar(select(Category).where(Category.id == category_id))

    def get_by_name(self, name: str) -> Category | None:
        return self.db.scalar(
            select(Category).where(Category.name_normalized == normalize_category_name(name))
        )

    def list_categories(
        self,
        *,
        search: str | None = None,
        is_public: bool | None = None,
    ) -> list[tuple[Category, int]]:
        """Devuelve (categoría, cantidad de productos), ordenadas por nombre."""
        product_count = (
            select(func.count(Product.id))
            .where(Product.category_id == Category.id)
            .correlate(Category)
            .scalar_subquery()
        )
        query = select(Category, product_count)

        if is_public is not None:
            query = query.where(Category.is_public.is_(is_public))

        if search and search.strip():
            query = query.where(Category.name.ilike(f"%{search.strip()}%"))

        query = query.order_by(Category.name_normalized.asc())
        return [(c, int(n or 0)) for c, n in self.db.execute(query).all()]

    def count_products(self, category_id: int) -> int:
        return int(
            self.db.scalar(select(func.count(Product.id)).where(Product.category_id == category_id)) or 0
        )

    # ------------------------------------------------------------- CREATE

    def _unique_slug(self, name: str, exclude_id: int | None = None) -> str:
        base = slugify(name) or "categoria"
        slug, n = base, 2
        while True:
            query = select(Category.id).where(Category.slug == slug)
            if exclude_id is not None:
                query = query.where(Category.id != exclude_id)
            if self.db.scalar(query) is None:
                return slug
            slug, n = f"{base}-{n}", n + 1

    def create(
        self,
        *,
        name: str,
        description: str | None = None,
        image_url: str | None = None,
        is_public: bool = True,
        requires_age_verification: bool = False,
    ) -> Category:
        name = " ".join(name.split())
        category = Category(
            name=name,
            name_normalized=normalize_category_name(name),
            slug=self._unique_slug(name),
            description=description,
            image_url=image_url,
            is_public=is_public,
            requires_age_verification=requires_age_verification,
        )
        self.db.add(category)
        self.db.flush()
        return category

    # ------------------------------------------------------------- UPDATE

    def update(self, category: Category, data: dict) -> Category:
        renamed = "name" in data and data["name"] is not None and data["name"] != category.name

        for field, value in data.items():
            if field == "name":
                if value is None:
                    continue
                category.name = value
                category.name_normalized = normalize_category_name(value)
            elif value is not None or field in ("description", "image_url"):
                setattr(category, field, value)

        if renamed:
            category.slug = self._unique_slug(category.name, exclude_id=category.id)

        self.db.flush()

        if renamed:
            # Products guarda una copia del nombre (búsquedas, analytics, exports).
            self.db.execute(
                update(Product)
                .where(Product.category_id == category.id)
                .values(category=category.name, category_normalized=category.name_normalized)
            )
            self.db.flush()
            self.db.expire_all()

        self.db.refresh(category)
        return category

    def delete(self, category: Category) -> None:
        self.db.delete(category)
        self.db.flush()

    # ------------------------------------------ uso desde productos / import

    def resolve_for_product(
        self,
        *,
        category_id: int | None,
        category_name: str | None,
    ) -> Category | None:
        """
        Resuelve la categoría de un producto:
        - category_id (la opción normal del panel): tiene que existir en el tenant.
        - category_name (importaciones / API legacy): se busca por nombre y, si no
          existe, se crea PRIVADA: nada se publica en el catálogo sin que la
          distribuidora lo decida.
        - ninguno (o "Sin Clasificar"): sin categoría.
        """
        if category_id is not None:
            category = self.get_by_id(category_id)
            if not category:
                raise ValueError(f"La categoría {category_id} no existe.")
            return category

        name = " ".join((category_name or "").split())
        if not name or normalize_category_name(name) in PLACEHOLDER_NAMES:
            return None

        existing = self.get_by_name(name)
        if existing:
            return existing

        return self.create(name=name, is_public=False)
