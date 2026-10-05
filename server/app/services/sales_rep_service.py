import math
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.constants.sales_rep_constant import (
    ALLOWED_SALES_REP_SORT_OPTIONS,
    ALLOWED_SALES_REP_STATUSES,
)
from app.core.security import create_access_token, get_password_hash, verify_password
from app.repositories.sales_rep_repository import SalesRepRepository
from app.schemas.sales_rep_schema import SalesRepCreate, SalesRepLogin, SalesRepUpdate
from app.utils.geo import validate_coordinates, compute_h3
from app.models.sales_rep_model import SalesRep

class SalesRepService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SalesRepRepository(db)
        
    @staticmethod
    def _validate_geo(lat, lng, coverage_radius_km) -> None:
        if (
            (lat is None and lng is not None)
            or
            (lat is not None and lng is None)
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="home_lat y home_lng deben enviarse juntos",
            )

        if coverage_radius_km is not None and (
            lat is None or lng is None
        ):
            raise HTTPException(
                status_code=400,
                detail="coverage_radius_km requiere coordenadas",
            )
        
        if lat is not None and lng is not None:
            try:
                validate_coordinates(lat, lng)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                )

    def get_by_id(self, sales_rep_id: int):
        sales_rep = self.repo.get_by_id(sales_rep_id)
        if not sales_rep:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendedor no encontrado",
            )
        return sales_rep

    def get_by_email(self, email: str):
        email = email.strip().lower()
        return self.repo.get_by_email(email)

    def get_sales_reps(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        status_filter: str | None = None,
        sort: str | None = None,
    ):
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="page debe ser mayor o igual a 1",
            )

        if page_size < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="page_size debe ser mayor o igual a 1",
            )
            
        if page_size > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="page_size no puede ser mayor a 20"
            )

        if status_filter is not None and status_filter not in ALLOWED_SALES_REP_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="status debe ser 'active', 'inactive' o vacío",
            )

        if sort is not None and sort not in ALLOWED_SALES_REP_SORT_OPTIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="sort debe ser 'name', 'created_at' o vacío",
            )
            
        if search:
            search = search.strip()

            if not search:
                search = None

        sales_reps, total = self.repo.get_sales_reps(
            page=page,
            page_size=page_size,
            search=search,
            status=status_filter,
            sort=sort,
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return {
            "sales_reps": sales_reps,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
        
    def create(
        self,
        data: SalesRepCreate,
        refresh: bool = True,
        tenant_id: int | None = None,
    ):
        existing_sales_rep = self.repo.get_by_email(data.email)

        if existing_sales_rep:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un vendedor con ese email",
            )

        self._validate_geo(
            data.home_lat,
            data.home_lng,
            data.coverage_radius_km,
        )

        home_h3_index = None

        if (
            data.home_lat is not None
            and
            data.home_lng is not None
        ):
            home_h3_index = compute_h3(
                data.home_lat,
                data.home_lng,
            )

        hashed_password = get_password_hash(
            data.password
        )

        return self.repo.create(
            data=data,
            hashed_password=hashed_password,
            home_h3_index=home_h3_index,
            refresh=refresh,
            tenant_id=tenant_id,
        )

    def update(
        self,
        sales_rep: SalesRep,
        data: SalesRepUpdate,
        refresh: bool = True,
    ) -> SalesRep:

        if data.email is not None:

            existing_sales_rep = self.repo.get_by_email(
                data.email
            )

            if (
                existing_sales_rep
                and
                existing_sales_rep.id != sales_rep.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe un vendedor con ese email",
                )

        if (
            "password" in data.model_fields_set
            and
            data.password
        ):
            sales_rep.hashed_password = get_password_hash(
                data.password
            )

        if (
            "home_lat" in data.model_fields_set
            or
            "home_lng" in data.model_fields_set
            or
            "coverage_radius_km" in data.model_fields_set
        ):

            lat = (
                data.home_lat
                if "home_lat" in data.model_fields_set
                else sales_rep.home_lat
            )

            lng = (
                data.home_lng
                if "home_lng" in data.model_fields_set
                else sales_rep.home_lng
            )

            coverage_radius_km = (
                data.coverage_radius_km
                if "coverage_radius_km" in data.model_fields_set
                else sales_rep.coverage_radius_km
            )

            self._validate_geo(
                lat,
                lng,
                coverage_radius_km,
            )

            home_h3_index = None

            if lat is None and lng is None:

                data.coverage_radius_km = None

            else:

                home_h3_index = compute_h3(
                    lat,
                    lng,
                )

            sales_rep.home_h3_index = home_h3_index

        return self.repo.update(
            sales_rep,
            data,
            refresh=refresh,
        )
        
    def update_by_id(
        self,
        sales_rep_id: int,
        data: SalesRepUpdate,
        refresh: bool = True,
    ) -> SalesRep:

        sales_rep = self.get_by_id(
            sales_rep_id
        )

        return self.update(
            sales_rep=sales_rep,
            data=data,
            refresh=refresh,
        )

    def update_password(
        self,
        sales_rep: SalesRep,
        new_password: str,
        refresh: bool = True,
    ) -> SalesRep:

        if (
            not new_password
            or
            len(new_password) < 6
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "La nueva contraseña "
                    "debe tener al menos 6 caracteres"
                ),
            )

        hashed_password = get_password_hash(
            new_password
        )

        return self.repo.update_password(
            sales_rep,
            hashed_password,
            refresh=refresh,
        )

    def update_password_by_id(
        self,
        sales_rep_id: int,
        new_password: str,
        refresh: bool = True,
    ) -> SalesRep:

        sales_rep = self.get_by_id(
            sales_rep_id
        )

        return self.update_password(
            sales_rep=sales_rep,
            new_password=new_password,
            refresh=refresh,
        )

    def deactivate(self, sales_rep_id: int):
        sales_rep = self.get_by_id(sales_rep_id)

        if not sales_rep.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El vendedor ya está inactivo",
            )

        return self.repo.deactivate(sales_rep)

    def activate(self, sales_rep_id: int):
        sales_rep = self.get_by_id(sales_rep_id)

        if sales_rep.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El vendedor ya está activo",
            )

        return self.repo.activate(sales_rep)

    def login(self, data: SalesRepLogin):
        sales_rep = self.repo.get_by_email(data.email)

        if not sales_rep or not verify_password(data.password, sales_rep.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
            )

        if not sales_rep.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El vendedor está inactivo",
            )

        access_token = create_access_token(
            subject=str(sales_rep.id),
            tenant_id=sales_rep.tenant_id,
        )

        return sales_rep, access_token