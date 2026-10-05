from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.category_model import Category
from app.repositories.category_repository import (
    PLACEHOLDER_NAMES,
    CategoryRepository,
    normalize_category_name,
)
from app.schemas.category_schema import (
    CategoryAdminResponse,
    CategoryCreate,
    CategoryListResponse,
    CategoryUpdate,
)



_INVALID_IMAGE_VALUES = {"nan", "none", "null", "n/a", "-"}


def has_valid_image(image_url: str | None) -> bool:
    """Misma regla que Product: vacío o valores basura (nan, null, -) no cuentan."""
    if not image_url:
        return False
    return image_url.strip().lower() not in _INVALID_IMAGE_VALUES


class CategoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CategoryRepository(db)

    @staticmethod
    def _require_image_if_public(is_public: bool, image_url: str | None) -> None:
        """Una categoría pública se muestra en la tienda: necesita imagen (como Product)."""
        if is_public and not has_valid_image(image_url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Para publicar una categoría en el catálogo necesita una imagen "
                    "(image_url). Cargá la imagen o dejá la categoría como privada."
                ),
            )

    # ---------------------------------------------------------------- GET

    def _get_or_404(self, category_id: int) -> Category:
        category = self.repo.get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categoría con ID {category_id} no encontrada",
            )
        return category

    def get_category(self, category_id: int, *, only_public: bool = False) -> Category:
        category = self._get_or_404(category_id)
        if only_public and not category.is_public:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categoría con ID {category_id} no encontrada",
            )
        return category

    def list_categories(
        self,
        *,
        search: str | None = None,
        is_public: bool | None = None,
        only_public: bool = False,
    ) -> CategoryListResponse:
        """only_public=True es la vista de un cliente: nunca ve categorías privadas."""
        if only_public:
            is_public = True

        rows = self.repo.list_categories(search=search, is_public=is_public)
        items = []
        for category, count in rows:
            item = CategoryAdminResponse.model_validate(category)
            item.product_count = count
            items.append(item)
        return CategoryListResponse(items=items, total=len(items))

    # ------------------------------------------------------------- CREATE

    def _ensure_name_available(self, name: str, exclude_id: int | None = None) -> None:
        normalized = normalize_category_name(name)
        if normalized in PLACEHOLDER_NAMES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'Sin Clasificar' es un valor reservado: no es una categoría.",
            )
        existing = self.repo.get_by_name(name)
        if existing and existing.id != exclude_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe una categoría llamada '{existing.name}'.",
            )

    def create_category(self, data: CategoryCreate) -> Category:
        self._ensure_name_available(data.name)
        self._require_image_if_public(data.is_public, data.image_url)
        return self.repo.create(
            name=data.name,
            description=data.description,
            image_url=data.image_url,
            is_public=data.is_public,
            requires_age_verification=data.requires_age_verification,
        )

    # ------------------------------------------------------------- UPDATE

    def update_category(self, category_id: int, data: CategoryUpdate) -> Category:
        category = self._get_or_404(category_id)
        update_data = data.model_dump(exclude_unset=True)

        if update_data.get("name"):
            self._ensure_name_available(update_data["name"], exclude_id=category.id)

        # Se valida el estado FINAL: no se puede dejar pública sin imagen, ya sea
        # publicándola sin imagen o quitándole la imagen a una pública.
        final_public = update_data.get("is_public")
        if final_public is None:
            final_public = category.is_public
        final_image = update_data["image_url"] if "image_url" in update_data else category.image_url
        self._require_image_if_public(final_public, final_image)

        return self.repo.update(category, update_data)

    def set_public(self, category_id: int, is_public: bool) -> Category:
        category = self._get_or_404(category_id)
        self._require_image_if_public(is_public, category.image_url)
        return self.repo.update(category, {"is_public": is_public})

    # ------------------------------------------------------------- DELETE

    def delete_category(self, category_id: int) -> None:
        category = self._get_or_404(category_id)
        count = self.repo.count_products(category.id)
        if count:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"La categoría tiene {count} producto(s). Movelos a otra categoría "
                    "o despublicá la categoría en lugar de borrarla."
                ),
            )
        self.repo.delete(category)
