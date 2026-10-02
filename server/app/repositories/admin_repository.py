from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.admin_model import Admin
from app.schemas.admin_schema import AdminCreate, AdminUpdate


class AdminRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        admin_id: int,
    ) -> Admin | None:
        stmt = select(Admin).where(
            Admin.id == admin_id
        )

        return self.db.scalar(stmt)

    def get_by_email(
        self,
        email: str,
    ) -> Admin | None:
        stmt = select(Admin).where(
            Admin.email == email
        )

        return self.db.scalar(stmt)

    def get_all(self) -> list[Admin]:
        stmt = select(Admin).order_by(
            Admin.created_at.desc()
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def create(
        self,
        data: AdminCreate,
        hashed_password: str,
        refresh: bool = True,
    ) -> Admin:

        admin = Admin(
            name=data.name,
            email=data.email,
            hashed_password=hashed_password,
            is_active=data.is_active,
        )

        self.db.add(admin)
        self.db.flush()

        if refresh:
            self.db.refresh(admin)

        return admin

    def update(
        self,
        admin: Admin,
        data: AdminUpdate,
        refresh: bool = True,
    ) -> Admin:

        update_data = data.model_dump(
            exclude_unset=True
        )

        update_data.pop("password", None)

        for field, value in update_data.items():
            setattr(admin, field, value)

        self.db.flush()

        if refresh:
            self.db.refresh(admin)

        return admin

    def update_password(
        self,
        admin: Admin,
        hashed_password: str,
        refresh: bool = True,
    ) -> Admin:

        admin.hashed_password = hashed_password

        self.db.flush()

        if refresh:
            self.db.refresh(admin)

        return admin

    def delete(
        self,
        admin: Admin,
    ) -> None:

        self.db.delete(admin)
        self.db.flush()