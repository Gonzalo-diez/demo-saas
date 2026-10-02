import secrets
from dataclasses import dataclass

from fastapi import Cookie, Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import get_db
from app.db.tenant_context import set_tenant
from app.models.client_model import Client
from app.models.sales_rep_model import SalesRep
from app.models.tenant_model import Tenant
from app.models.admin_model import Admin
from app.repositories.client_repository import ClientRepository
from app.repositories.sales_rep_repository import SalesRepRepository
from app.repositories.tenant_repository import TenantRepository
from app.repositories.admin_repository import AdminRepository

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)


def _decode_token(token: str) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
    )
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except JWTError:
        raise credentials_exception


# ----------------------------------------------------------------------
# TENANT
#
# Regla de oro: en requests autenticados el tenant sale SIEMPRE del claim
# "tenant_id" del JWT. Los headers X-Tenant-Slug / X-Tenant-ID solo se usan
# donde todavía no hay token (login, tracking público del catálogo).
#
# Resolver el tenant deja la sesión "atada" a él (set_tenant): desde ahí
# todas las consultas del request quedan filtradas por tenant_id
# automáticamente (ver app/db/tenant_context.py).
# ----------------------------------------------------------------------

def _ensure_tenant_active(tenant: Tenant) -> Tenant:
    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El Tenant se encuentra inactivo",
        )
    return tenant


def _bind_tenant_from_payload(db: Session, payload: dict, exc: HTTPException) -> Tenant:
    """Valida el claim tenant_id del token y ata la sesión a ese tenant."""
    raw_tenant_id = payload.get("tenant_id")
    if raw_tenant_id is None:
        # Token sin tenant (emitido antes de multi-tenant): no sirve.
        raise exc
    try:
        tenant_id = int(raw_tenant_id)
    except (TypeError, ValueError):
        raise exc

    tenant = TenantRepository(db).get_by_id(tenant_id)
    if tenant is None:
        raise exc
    _ensure_tenant_active(tenant)

    set_tenant(db, tenant.id)
    return tenant


@dataclass(frozen=True)
class TenantRef:
    """Referencia a un tenant mandada por el cliente (solo para endpoints sin token)."""
    slug: str | None = None
    id: int | None = None


def get_tenant_ref(
    x_tenant_slug: str | None = Header(default=None, alias="X-Tenant-Slug"),
    x_tenant_id: int | None = Header(default=None, alias="X-Tenant-ID"),
) -> TenantRef:
    return TenantRef(slug=x_tenant_slug, id=x_tenant_id)


def bind_tenant_from_ref(
    db: Session,
    ref: TenantRef,
    body_slug: str | None = None,
) -> Tenant:
    """
    Resuelve el tenant por slug (body > header) o por id (header) y ata la
    sesión. SOLO para endpoints sin autenticación (login, tracking público).
    """
    slug = (body_slug or ref.slug or "").strip().lower() or None

    repo = TenantRepository(db)
    tenant: Tenant | None = None
    if slug is not None:
        tenant = repo.get_by_slug(slug)
    elif ref.id is not None:
        tenant = repo.get_by_id(ref.id)

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se especificó o no se encontró el Tenant (header X-Tenant-Slug)",
        )
    _ensure_tenant_active(tenant)

    set_tenant(db, tenant.id)
    return tenant


def get_login_tenant(
    ref: TenantRef = Depends(get_tenant_ref),
    db: Session = Depends(get_db),
) -> Tenant:
    """Tenant para endpoints de login: solo por header (ignora cualquier cookie previa)."""
    return bind_tenant_from_ref(db, ref)


def get_public_tenant(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_cookie: str | None = Cookie(default=None, alias=settings.AUTH_COOKIE_NAME),
    client_auth_cookie: str | None = Cookie(default=None, alias=settings.CLIENT_AUTH_COOKIE_NAME),
    ref: TenantRef = Depends(get_tenant_ref),
    db: Session = Depends(get_db),
) -> Tenant:
    """
    Tenant para endpoints sin login obligatorio (ej. tracking del catálogo):
    si viene un token válido manda su tenant; si no, el header X-Tenant-Slug.
    """
    token = client_auth_cookie or auth_cookie or (credentials.credentials if credentials else None)
    if token:
        try:
            payload = _decode_token(token)
            return _bind_tenant_from_payload(
                db,
                payload,
                HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"),
            )
        except HTTPException:
            pass  # token vencido/inválido: caemos al header
    return bind_tenant_from_ref(db, ref)


def get_current_tenant(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_cookie: str | None = Cookie(default=None, alias=settings.AUTH_COOKIE_NAME),
    client_auth_cookie: str | None = Cookie(default=None, alias=settings.CLIENT_AUTH_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> Tenant:
    """Tenant del usuario autenticado (staff o cliente), tomado del JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
    )
    token = client_auth_cookie or auth_cookie or (credentials.credentials if credentials else None)
    if not token:
        raise credentials_exception
    payload = _decode_token(token)
    return _bind_tenant_from_payload(db, payload, credentials_exception)


def get_current_active_tenant(
    current_tenant: Tenant = Depends(get_current_tenant),
) -> Tenant:
    """Garantiza que el Tenant resuelto esté activo."""
    return _ensure_tenant_active(current_tenant)


# ----------------------------------------------------------------------
# PLATFORM ADMIN (alta/baja de distribuidoras)
# ----------------------------------------------------------------------

def require_platform_admin(
    x_platform_key: str | None = Header(default=None, alias="X-Platform-Key"),
) -> None:
    expected = settings.PLATFORM_ADMIN_KEY
    if not expected or not x_platform_key or not secrets.compare_digest(
        x_platform_key.encode("utf-8"), expected.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere la clave de administración de la plataforma",
        )


# ----------------------------------------------------------------------
# USER DEPENDENCIES
# ----------------------------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_cookie: str | None = Cookie(default=None, alias=settings.AUTH_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> SalesRep:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
    )

    token = auth_cookie or (credentials.credentials if credentials else None)
    if not token:
        raise credentials_exception

    try:
        payload = _decode_token(token)
        if payload.get("type", "staff") != "staff":
            raise credentials_exception

        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        user_id = int(user_id)
    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    _bind_tenant_from_payload(db, payload, credentials_exception)

    # Ya filtrado por el tenant del token: un id de otra distribuidora no aparece.
    repo = SalesRepRepository(db)
    sales_rep = repo.get_by_id(user_id)

    if sales_rep is None:
        raise credentials_exception

    return sales_rep


def get_current_active_user(
    current_sales_rep: SalesRep = Depends(get_current_user),
) -> SalesRep:
    if not current_sales_rep.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )
    return current_sales_rep


def get_current_superuser(
    current_sales_rep: SalesRep = Depends(get_current_active_user),
) -> SalesRep:
    if not current_sales_rep.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes",
        )
    return current_sales_rep


# ----------------------------------------------------------------------
# CLIENT DEPENDENCIES
# ----------------------------------------------------------------------

def get_current_client(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    client_auth_cookie: str | None = Cookie(default=None, alias=settings.CLIENT_AUTH_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> Client:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Debés iniciar sesión para acceder al catálogo",
    )

    token = client_auth_cookie or (credentials.credentials if credentials else None)
    if not token:
        raise credentials_exception

    try:
        payload = _decode_token(token)
        if payload.get("type") != "client":
            raise credentials_exception

        client_id = payload.get("sub")
        if client_id is None:
            raise credentials_exception

        client_id = int(client_id)
    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    _bind_tenant_from_payload(db, payload, credentials_exception)

    repo = ClientRepository(db)
    client = repo.get_by_id(client_id)

    if client is None:
        raise credentials_exception

    return client


def get_current_active_client(
    current_client: Client = Depends(get_current_client),
) -> Client:
    if not current_client.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cliente inactivo",
        )
    return current_client


def get_current_catalog_viewer(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_cookie: str | None = Cookie(default=None, alias=settings.AUTH_COOKIE_NAME),
    client_auth_cookie: str | None = Cookie(default=None, alias=settings.CLIENT_AUTH_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> SalesRep | Client:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Debés iniciar sesión para ver el catálogo",
    )

    token = client_auth_cookie or auth_cookie
    if not token and credentials is not None:
        token = credentials.credentials

    if not token:
        raise credentials_exception

    try:
        payload = _decode_token(token)
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception
        subject_id = int(subject)
        token_type = payload.get("type", "staff")
    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    _bind_tenant_from_payload(db, payload, credentials_exception)

    if token_type == "client":
        client_repo = ClientRepository(db)
        client = client_repo.get_by_id(subject_id)
        if client is None or not client.is_active:
            raise credentials_exception
        return client

    sales_rep_repo = SalesRepRepository(db)
    sales_rep = sales_rep_repo.get_by_id(subject_id)
    if sales_rep is None or not sales_rep.is_active:
        raise credentials_exception
    return sales_rep

# ----------------------------------------------------------------------
# PLATFORM ADMIN DEPENDENCIES
# ----------------------------------------------------------------------

def get_current_platform_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    platform_auth_cookie: str | None = Cookie(
        default=None,
        alias=settings.PLATFORM_AUTH_COOKIE_NAME,
    ),
    db: Session = Depends(get_db),
) -> Admin:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
    )

    token = (
        platform_auth_cookie
        or (
            credentials.credentials
            if credentials
            else None
        )
    )

    if not token:
        raise credentials_exception

    payload = _decode_token(token)

    if payload.get("type") != "platform_admin":
        raise credentials_exception

    admin_id = payload.get("sub")

    if admin_id is None:
        raise credentials_exception

    try:
        admin_id = int(admin_id)
    except (ValueError, TypeError):
        raise credentials_exception

    admin = AdminRepository(db).get_by_id(
        admin_id
    )

    if not admin:
        raise credentials_exception

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrador inactivo",
        )

    return admin