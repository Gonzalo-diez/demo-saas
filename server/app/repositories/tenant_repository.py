from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.tenant_model import Tenant
from app.schemas.tenant_schema import TenantCreate, TenantUpdate


class TenantRepository:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------

    def get_by_id(self, tenant_id: int) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        return self.db.scalar(stmt)

    def get_by_slug(self, slug: str) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.slug == slug)
        return self.db.scalar(stmt)

    def get_by_name(self, name: str) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.name.ilike(name.strip()))
        return self.db.scalar(stmt)

    def get_tenants(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
        sort: str | None = None,
    ) -> tuple[list[Tenant], int]:

        stmt = select(Tenant)
        count_stmt = select(func.count()).select_from(Tenant)

        # Search
        if search:
            search_term = f"%{search.strip()}%"
            search_filter = or_(
                Tenant.name.ilike(search_term),
                Tenant.slug.ilike(search_term),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        # Filter by active state
        if is_active is not None:
            active_filter = Tenant.is_active.is_(is_active)
            stmt = stmt.where(active_filter)
            count_stmt = count_stmt.where(active_filter)

        # Sort
        normalized_sort = (sort or "").strip().lower()
        if normalized_sort == "name":
            stmt = stmt.order_by(Tenant.name.asc())
        elif normalized_sort == "slug":
            stmt = stmt.order_by(Tenant.slug.asc())
        else:
            stmt = stmt.order_by(Tenant.created_at.desc())

        # Count total
        total = self.db.scalar(count_stmt) or 0

        # Pagination
        tenants = list(
            self.db.scalars(
                stmt.offset((page - 1) * page_size).limit(page_size)
            ).all()
        )

        return tenants, total

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    def create(
        self,
        data: TenantCreate,
        refresh: bool = True,
    ) -> Tenant:
        payload = data.model_dump()
        tenant = Tenant(**payload)

        self.db.add(tenant)
        self.db.flush()

        if refresh:
            self.db.refresh(tenant)

        return tenant

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    def update(
        self,
        tenant: Tenant,
        data: TenantUpdate,
        refresh: bool = True,
    ) -> Tenant:
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(tenant, field, value)

        self.db.flush()

        if refresh:
            self.db.refresh(tenant)

        return tenant

    # ------------------------------------------------------------------
    # ACTIVATE / DEACTIVATE
    # ------------------------------------------------------------------

    def activate(self, tenant: Tenant, refresh: bool = True) -> Tenant:
        tenant.is_active = True
        self.db.flush()
        if refresh:
            self.db.refresh(tenant)
        return tenant

    def deactivate(self, tenant: Tenant, refresh: bool = True) -> Tenant:
        tenant.is_active = False
        self.db.flush()
        if refresh:
            self.db.refresh(tenant)
        return tenant