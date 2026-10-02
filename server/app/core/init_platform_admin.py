from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.repositories.admin_repository import AdminRepository
from app.schemas.admin_schema import AdminCreate
from app.services.admin_service import AdminService


def create_first_platform_admin(
    db: Session,
) -> None:

    inspector = inspect(db.bind)

    if "admins" not in inspector.get_table_names():
        print(
            "⚠️ [INIT-ADMIN] La tabla 'admins' "
            "todavía no existe."
        )
        return

    settings = get_settings()

    if (
        not settings.FIRST_ADMIN_EMAIL
        or not settings.FIRST_ADMIN_PASSWORD
    ):
        print(
            "⚠️ [INIT-ADMIN] "
            "Faltan FIRST_ADMIN_EMAIL "
            "o FIRST_ADMIN_PASSWORD."
        )
        return

    repo = AdminRepository(db)

    existing = repo.get_by_email(
        settings.FIRST_ADMIN_EMAIL
    )

    if existing:
        print(
            "ℹ️ [INIT-ADMIN] "
            "El admin inicial ya existe."
        )
        return

    service = AdminService(db)

    service.create(
        AdminCreate(
            name=settings.FIRST_ADMIN_NAME,
            email=settings.FIRST_ADMIN_EMAIL,
            password=settings.FIRST_ADMIN_PASSWORD,
            is_active=True,
        )
    )

    print(
        "🚀 [INIT-ADMIN] "
        "Admin de plataforma creado correctamente."
    )