from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.tenant_context import tenant_scope
from app.repositories.sales_rep_repository import SalesRepRepository
from app.repositories.tenant_repository import TenantRepository
from app.schemas.sales_rep_schema import SalesRepCreate
from app.schemas.tenant_schema import TenantCreate
from app.services.sales_rep_service import SalesRepService
from app.services.tenant_service import TenantService


def create_first_tenant(db: Session):
    print("🔍 [INIT-TENANT] Iniciando verificación de tenant inicial...")
    inspector = inspect(db.bind)

    # Verificación de Tablas
    if "tenants" not in inspector.get_table_names():
        print("⚠️ [INIT-TENANT] Cancelado: La tabla 'tenants' no existe en la DB. ¿Corriste las migraciones?")
        return None

    settings = get_settings()

    tenant_name = settings.FIRST_TENANT_NAME
    tenant_slug = settings.FIRST_TENANT_SLUG
    tenant_email = settings.FIRST_TENANT_EMAIL or settings.FIRST_SUPERUSER_EMAIL

    repo = TenantRepository(db)
    existing = repo.get_by_slug(tenant_slug)

    if existing:
        print(f"ℹ️ [INIT-TENANT] El tenant inicial ('{tenant_slug}') ya existe. No se requiere acción.")
        return existing

    print(f"⚡ [INIT-TENANT] Creando tenant inicial ('{tenant_name}' - '{tenant_slug}')...")
    try:
        service = TenantService(db)
        tenant = service.create(
            TenantCreate(
                name=tenant_name,
                slug=tenant_slug,
                email=tenant_email,
                is_active=True,
            )
        )
        print("🚀 [INIT-TENANT] ¡Tenant inicial creado con éxito!")
        return tenant
    except Exception as e:
        db.rollback()
        print(f"❌ [INIT-TENANT] Error al insertar el tenant en la DB: {e}")
        return None


def create_first_superuser(db: Session, tenant_id: int | None = None) -> None:
    print("🔍 [INIT-ADMIN] Iniciando verificación de superusuario...")
    inspector = inspect(db.bind)

    # Verificación de Tablas
    if "sales_reps" not in inspector.get_table_names():
        print("⚠️ [INIT-ADMIN] Cancelado: La tabla 'sales_reps' no existe en la DB. ¿Corriste las migraciones?")
        return

    settings = get_settings()

    # Verificación de Variables de Entorno
    if not settings.FIRST_SUPERUSER_EMAIL or not settings.FIRST_SUPERUSER_PASSWORD:
        print(
            f"⚠️ [INIT-ADMIN] Cancelado: Faltan credenciales en el .env "
            f"(EMAIL: '{settings.FIRST_SUPERUSER_EMAIL}', PASSWORD: {'Configurada' if settings.FIRST_SUPERUSER_PASSWORD else 'Vacía'})"
        )
        return

    # Si no nos pasaron el tenant_id, usamos el del tenant inicial
    if tenant_id is None:
        tenant = TenantRepository(db).get_by_slug(settings.FIRST_TENANT_SLUG)
        if not tenant:
            print("⚠️ [INIT-ADMIN] Cancelado: No se encontró un tenant inicial para asociar al superusuario.")
            return
        tenant_id = tenant.id

    try:
        # El email es único POR tenant: se busca y se crea dentro del tenant inicial.
        with tenant_scope(db, tenant_id):
            if SalesRepRepository(db).get_by_email(settings.FIRST_SUPERUSER_EMAIL):
                print("ℹ️ [INIT-ADMIN] El superusuario ya existe. No se requiere acción.")
                return

            print("⚡ [INIT-ADMIN] Creando primer superusuario...")
            SalesRepService(db).create(
                SalesRepCreate(
                    name="Admin",
                    email=settings.FIRST_SUPERUSER_EMAIL,
                    password=settings.FIRST_SUPERUSER_PASSWORD,
                    is_superuser=True,
                    is_active=True,
                ),
                tenant_id=tenant_id,
            )
            db.commit()
        print("🚀 [INIT-ADMIN] ¡Primer superusuario creado con éxito!")
    except Exception as e:
        db.rollback()
        print(f"❌ [INIT-ADMIN] Error al insertar en la DB: {e}")


def init_db(db: Session) -> None:
    """Función orquestadora para inicializar los datos base de la aplicación."""
    tenant = create_first_tenant(db)
    if tenant:
        create_first_superuser(db, tenant_id=tenant.id)
    else:
        print("⚠️ [INIT-ADMIN] Cancelado: No se pudo obtener ni crear el tenant inicial.")
