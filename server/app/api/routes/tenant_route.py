from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_tenant, get_current_platform_admin
from app.db.base import get_db
from app.models.tenant_model import Tenant
from app.schemas.tenant_schema import (
    PaginatedTenantResponse,
    TenantProvision,
    TenantPublicResponse,
    TenantResponse,
    TenantUpdate,
)
from app.services.tenant_service import TenantService

router = APIRouter(prefix="/tenants", tags=["Tenants"])


def get_tenant_service(db: Session = Depends(get_db)) -> TenantService:
    return TenantService(db)


ServiceDep = Annotated[TenantService, Depends(get_tenant_service)]

# La gestión de distribuidoras (alta, baja, listado) es de la PLATAFORMA, no de
# una distribuidora: la hace un administrador de la tabla admins (login en
# /api/admin/login). Ni un vendedor ni un cliente de un tenant pasan.
PlatformAdmin = [Depends(get_current_platform_admin)]


# ----------------------------------------------------------------------
# Públicos / del propio tenant
# ----------------------------------------------------------------------

@router.get(
    "/slug/{slug}",
    response_model=TenantPublicResponse,
    status_code=status.HTTP_200_OK,
    summary="Datos públicos de una distribuidora (login / branding)",
)
def get_tenant_by_slug(slug: str, service: ServiceDep):
    tenant = service.get_by_slug(slug.strip().lower())
    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado",
        )
    return tenant


@router.get(
    "/by-domain/{domain}",
    response_model=TenantPublicResponse,
    status_code=status.HTTP_200_OK,
    summary="Distribuidora dueña de un dominio (la tienda pública la usa para identificarse)",
)
def get_tenant_by_domain(domain: str, service: ServiceDep):
    """
    `domain` es el host con el que el cliente entró a la tienda
    (ej. tienda.distri-norte.com). Devuelve name/slug/logo para armar la página.
    """
    tenant = service.get_by_domain(domain)
    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant no encontrado",
        )
    return tenant


@router.get(
    "/me",
    response_model=TenantResponse,
    status_code=status.HTTP_200_OK,
    summary="Tenant del usuario autenticado",
)
def get_my_tenant(tenant: Tenant = Depends(get_current_active_tenant)):
    return tenant


# ----------------------------------------------------------------------
# Administración de la plataforma (admin de plataforma logueado)
# ----------------------------------------------------------------------

@router.get(
    "/",
    response_model=PaginatedTenantResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar tenants con paginación y filtros",
    dependencies=PlatformAdmin,
)
def get_tenants(
    service: ServiceDep,
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=20, ge=1, le=100, description="Registros por página"),
    search: str | None = Query(default=None, description="Búsqueda por nombre o slug"),
    is_active: bool | None = Query(default=None, description="Filtrar por estado activo"),
    sort: str | None = Query(default=None, description="Ordenar por: name, slug, created_at"),
):
    items, total = service.get_tenants(
        page=page,
        page_size=page_size,
        search=search,
        is_active=is_active,
        sort=sort,
    )
    return PaginatedTenantResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener tenant por ID",
    dependencies=PlatformAdmin,
)
def get_tenant_by_id(tenant_id: int, service: ServiceDep):
    return service.get_by_id(tenant_id)


@router.post(
    "/",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una distribuidora (opcionalmente con su primer administrador)",
    dependencies=PlatformAdmin,
)
def create_tenant(data: TenantProvision, service: ServiceDep):
    return service.provision(data)


@router.patch(
    "/{tenant_id}",
    response_model=TenantResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar parcialmente un tenant",
    dependencies=PlatformAdmin,
)
def update_tenant(tenant_id: int, data: TenantUpdate, service: ServiceDep):
    return service.update(tenant_id, data)


@router.patch(
    "/{tenant_id}/activate",
    response_model=TenantResponse,
    status_code=status.HTTP_200_OK,
    summary="Activar un tenant",
    dependencies=PlatformAdmin,
)
def activate_tenant(tenant_id: int, service: ServiceDep):
    return service.activate(tenant_id)


@router.patch(
    "/{tenant_id}/deactivate",
    response_model=TenantResponse,
    status_code=status.HTTP_200_OK,
    summary="Desactivar un tenant",
    dependencies=PlatformAdmin,
)
def deactivate_tenant(tenant_id: int, service: ServiceDep):
    return service.deactivate(tenant_id)
