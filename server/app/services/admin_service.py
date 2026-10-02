from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.models.admin_model import Admin
from app.repositories.admin_repository import AdminRepository
from app.schemas.admin_schema import (
    AdminCreate,
    AdminLogin,
    AdminUpdate,
)


class AdminService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AdminRepository(db)

    def get_by_id(
        self,
        admin_id: int,
    ) -> Admin:

        admin = self.repo.get_by_id(admin_id)

        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin no encontrado",
            )

        return admin

    def get_all(self) -> list[Admin]:
        return self.repo.get_all()

    def create(
        self,
        data: AdminCreate,
    ) -> Admin:

        existing = self.repo.get_by_email(
            data.email
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un admin con ese email",
            )

        admin = self.repo.create(
            data=data,
            hashed_password=get_password_hash(
                data.password
            ),
            refresh=False,
        )

        self.db.commit()
        self.db.refresh(admin)

        return admin

    def update(
        self,
        admin_id: int,
        data: AdminUpdate,
    ) -> Admin:

        admin = self.get_by_id(admin_id)

        if data.email is not None:

            existing = self.repo.get_by_email(
                data.email
            )

            if (
                existing
                and existing.id != admin.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe un admin con ese email",
                )

        if (
            "password" in data.model_fields_set
            and data.password
        ):
            self.repo.update_password(
                admin,
                get_password_hash(data.password),
                refresh=False,
            )

        self.repo.update(
            admin,
            data,
            refresh=False,
        )

        self.db.commit()
        self.db.refresh(admin)

        return admin

    def login(
        self,
        data: AdminLogin,
    ) -> tuple[Admin, str]:

        admin = self.repo.get_by_email(
            data.email
        )

        if (
            not admin
            or not verify_password(
                data.password,
                admin.hashed_password,
            )
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
            )

        if not admin.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El administrador está inactivo",
            )

        access_token = create_access_token(
            subject=str(admin.id),
            token_type="platform_admin",
        )

        return admin, access_token

    def delete(
        self,
        admin_id: int,
    ) -> None:

        admin = self.get_by_id(admin_id)

        self.repo.delete(admin)

        self.db.commit()