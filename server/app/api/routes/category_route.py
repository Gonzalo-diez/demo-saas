from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_optional_catalog_viewer
from app.db.base import get_db, get_db_with_commit
from app.models.client_model import Client
from app.models.sales_rep_model import SalesRep
from app.schemas.category_schema import (
    CategoryAdminResponse,
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdate,
)
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/", response_model=CategoryListResponse)
def list_categories(
    search: str | None = Query(None, max_length=100),
    is_public: bool | None = Query(None),
    db: Session = Depends(get_db),
    viewer: SalesRep | Client | None = Depends(get_optional_catalog_viewer),
):
    """
    Categorías de la distribuidora. El personal ve todas (con cantidad de productos);
    un cliente o visitante (sin login) solo ve las públicas, sin importar el filtro que mande.
    """
    service = CategoryService(db)
    return service.list_categories(
        search=search,
        is_public=is_public,
        only_public=not isinstance(viewer, SalesRep),
    )


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    """Crea una categoría propia. is_public decide si los clientes la ven."""
    return CategoryService(db).create_category(data)


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    viewer: SalesRep | Client | None = Depends(get_optional_catalog_viewer),
):
    return CategoryService(db).get_category(
        category_id, only_public=not isinstance(viewer, SalesRep)
    )


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    """Renombra / cambia descripción, publicación o verificación de edad."""
    return CategoryService(db).update_category(category_id, data)


@router.patch("/{category_id}/publish", response_model=CategoryResponse)
def publish_category(
    category_id: int,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    """La categoría (y sus productos publicados) pasa a verse en el catálogo."""
    return CategoryService(db).set_public(category_id, True)


@router.patch("/{category_id}/unpublish", response_model=CategoryResponse)
def unpublish_category(
    category_id: int,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    """Oculta la categoría y todos sus productos del catálogo de clientes."""
    return CategoryService(db).set_public(category_id, False)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    """Solo se puede borrar una categoría sin productos."""
    CategoryService(db).delete_category(category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
