from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.models.sales_rep_model import SalesRep
from app.schemas.sales_rep_schema import SalesRepCreate, SalesRepUpdate

class SalesRepRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def get_all(self) -> list[SalesRep]:
        stmt = select(SalesRep)
        return list(self.db.scalars(stmt).all())

    def get_by_id(self, sales_rep_id: int) -> SalesRep | None:
        stmt = select(SalesRep).where(SalesRep.id == sales_rep_id)
        return self.db.scalar(stmt)

    def get_by_email(self, email: str) -> SalesRep | None:
        stmt = select(SalesRep).where(SalesRep.email == email)
        return self.db.scalar(stmt)

    def get_by_name(self, name: str) -> SalesRep | None:
        """
        Matchea por nombre ignorando mayúsculas/espacios — se usa para
        corroborar vendedores cuando lo único que tenemos es el nombre
        (ej.: el nombre de una pestaña del Excel de importación).
        """
        normalized_name = "".join(name.strip().lower().split())

        stmt = select(SalesRep).where(
            func.replace(
                func.lower(SalesRep.name),
                " ",
                "",
            )
            == normalized_name
        )

        return self.db.scalar(stmt)
    
    def get_by_emails(
        self,
        emails: list[str],
    ) -> list[SalesRep]:

        stmt = select(SalesRep).where(
            SalesRep.email.in_(emails)
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def get_sales_reps(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        status: str | None = None,
        sort: str | None = None,
    ) -> tuple[list[SalesRep], int]:
        stmt = select(SalesRep)
        count_stmt = select(func.count()).select_from(SalesRep)

        if search:
            search_term = f"%{search.strip()}%"
            search_filter = or_(
                SalesRep.name.ilike(search_term),
                SalesRep.email.ilike(search_term),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        if status == "active":
            status_filter = SalesRep.is_active.is_(True)
            stmt = stmt.where(status_filter)
            count_stmt = count_stmt.where(status_filter)
        elif status == "inactive":
            status_filter = SalesRep.is_active.is_(False)
            stmt = stmt.where(status_filter)
            count_stmt = count_stmt.where(status_filter)

        if sort == "name":
            stmt = stmt.order_by(SalesRep.name.asc())
        elif sort == "created_at":
            stmt = stmt.order_by(SalesRep.created_at.desc())
        else:
            stmt = stmt.order_by(SalesRep.created_at.desc())

        total = self.db.scalar(count_stmt) or 0
        sales_reps = list(
            self.db.scalars(
                stmt.offset((page - 1) * page_size).limit(page_size)
            ).all()
        )

        return sales_reps, total

    def create(
        self,
        data: SalesRepCreate,
        hashed_password: str,
        home_h3_index: str | None,
        refresh: bool = True,
        tenant_id: int | None = None
    ) -> SalesRep:

        # tenant_id solo lo pasa código de sistema (alta de tenant, seeds); en
        # requests normales queda None y la sesión lo completa con el tenant activo.
        sales_rep = SalesRep(
            tenant_id=tenant_id,
            name=data.name,
            email=data.email,
            phone=data.phone,
            hashed_password=hashed_password,
            is_active=data.is_active,
            is_superuser=data.is_superuser,
            home_lat=data.home_lat,
            home_lng=data.home_lng,
            coverage_radius_km=data.coverage_radius_km,
            home_h3_index=home_h3_index,
        )

        self.db.add(sales_rep)
        self.db.flush()
        if refresh:
            self.db.refresh(sales_rep)

        return sales_rep
    
    def update(
        self,
        sales_rep: SalesRep,
        data: SalesRepUpdate,
        refresh: bool = True,
    ) -> SalesRep:

        update_data = data.model_dump(exclude_unset=True)

        # password no es un atributo del modelo (solo existe hashed_password).
        # Se hashea y asigna aparte en SalesRepService.update(), así que acá
        # lo descartamos para no pisarlo con texto plano ni dejar un atributo
        # suelto sin efecto.
        update_data.pop("password", None)

        for field, value in update_data.items():
            setattr(sales_rep, field, value)

        self.db.flush()
        
        if refresh:
            self.db.refresh(sales_rep)

        return sales_rep

    def get_sales_reps_for_map(
        self,
        search: str | None = None,
        is_active: bool | None = None,
        h3_indexes: list[str] | None = None,
    ) -> list[SalesRep]:

        stmt = select(SalesRep).where(
            SalesRep.home_lat.is_not(None),
            SalesRep.home_lng.is_not(None),
        )

        if search:
            search_term = f"%{search.strip()}%"

            stmt = stmt.where(
                or_(
                    SalesRep.name.ilike(search_term),
                    SalesRep.email.ilike(search_term),
                    SalesRep.phone.ilike(search_term),
                )
            )

        if is_active is not None:
            stmt = stmt.where(
                SalesRep.is_active.is_(is_active)
            )

        # filtro geo H3
        if h3_indexes:
            stmt = stmt.where(
                SalesRep.home_h3_index.in_(h3_indexes)
            )

        stmt = stmt.order_by(
            SalesRep.name.asc()
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def update_password(
        self,
        sales_rep: SalesRep,
        hashed_password: str,
        refresh: bool = True,
    ) -> SalesRep:

        sales_rep.hashed_password = hashed_password
        
        self.db.flush()
        
        if refresh:
            self.db.refresh(sales_rep)

        return sales_rep

    def deactivate(self, sales_rep: SalesRep) -> SalesRep:
        sales_rep.is_active = False
        self.db.flush()
        self.db.refresh(sales_rep)
        return sales_rep

    def activate(self, sales_rep: SalesRep) -> SalesRep:
        sales_rep.is_active = True
        self.db.flush()
        self.db.refresh(sales_rep)
        return sales_rep