from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.tenant_model import Tenant
from app.repositories.tenant_repository import TenantRepository
from app.db.tenant_context import tenant_scope
from app.schemas.sales_rep_schema import SalesRepCreate
from app.schemas.tenant_schema import TenantCreate, TenantProvision, TenantUpdate


class TenantService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = TenantRepository(db)

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------

    def get_by_id(self, tenant_id: int) -> Tenant:
        tenant = self.repository.get_by_id(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant con ID {tenant_id} no encontrado",
            )
        return tenant

    def get_by_slug(self, slug: str) -> Tenant:
        tenant = self.repository.get_by_slug(slug)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant con slug '{slug}' no encontrado",
            )
        return tenant

    def get_tenants(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
        sort: str | None = None,
    ) -> tuple[list[Tenant], int]:
        return self.repository.get_tenants(
            page=page,
            page_size=page_size,
            search=search,
            is_active=is_active,
            sort=sort,
        )

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    def _validate_unique(self, data: TenantCreate) -> None:
        # Validación de negocio: Slug único
        if self.repository.get_by_slug(data.slug):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El slug '{data.slug}' ya está en uso",
            )

        # Validación de negocio: Nombre único
        if self.repository.get_by_name(data.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El tenant con el nombre '{data.name}' ya existe",
            )

    def create(self, data: TenantCreate) -> Tenant:
        self._validate_unique(data)

        tenant = self.repository.create(data, refresh=False)
        self.db.commit()
        self.db.refresh(tenant)
        return tenant

    def provision(self, data: TenantProvision) -> Tenant:
        """
        Alta de una distribuidora nueva (+ su primer administrador, si se
        envían admin_email/admin_password). Todo en una sola transacción: si
        falla el admin, no queda un tenant huérfano.
        """
        from app.services.sales_rep_service import SalesRepService

        tenant_data = TenantCreate(**data.model_dump(include=set(TenantCreate.model_fields)))
        self._validate_unique(tenant_data)

        try:
            tenant = self.repository.create(tenant_data, refresh=False)

            if data.admin_email and data.admin_password:
                # El usuario nace dentro del tenant nuevo: la sesión se ata a él
                # mientras se crea (el email se valida contra ese tenant).
                with tenant_scope(self.db, tenant.id):
                    SalesRepService(self.db).create(
                        SalesRepCreate(
                            name=data.admin_name or "Admin",
                            email=data.admin_email,
                            password=data.admin_password,
                            is_superuser=True,
                            is_active=True,
                        ),
                        refresh=False,
                        tenant_id=tenant.id,
                    )

            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(tenant)
        return tenant

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    def update(self, tenant_id: int, data: TenantUpdate) -> Tenant:
        tenant = self.get_by_id(tenant_id)

        # Validación de negocio: Validar duplicado de slug solo si cambió
        if data.slug is not None and data.slug != tenant.slug:
            if self.repository.get_by_slug(data.slug):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"El slug '{data.slug}' ya está en uso",
                )

        # Validación de negocio: Validar duplicado de nombre solo si cambió
        if data.name is not None and data.name.strip().lower() != tenant.name.lower():
            if self.repository.get_by_name(data.name):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"El tenant con el nombre '{data.name}' ya existe",
                )

        updated_tenant = self.repository.update(tenant, data, refresh=False)
        self.db.commit()
        self.db.refresh(updated_tenant)
        return updated_tenant

    # ------------------------------------------------------------------
    # ACTIVATE / DEACTIVATE
    # ------------------------------------------------------------------

    def activate(self, tenant_id: int) -> Tenant:
        tenant = self.get_by_id(tenant_id)

        if tenant.is_active:
            return tenant

        activated_tenant = self.repository.activate(tenant, refresh=False)
        self.db.commit()
        self.db.refresh(activated_tenant)
        return activated_tenant

    def deactivate(self, tenant_id: int) -> Tenant:
        tenant = self.get_by_id(tenant_id)

        if not tenant.is_active:
            return tenant

        deactivated_tenant = self.repository.deactivate(tenant, refresh=False)
        self.db.commit()
        self.db.refresh(deactivated_tenant)
        return deactivated_tenant