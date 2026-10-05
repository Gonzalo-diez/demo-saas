from dataclasses import dataclass

from fastapi import Cookie, Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import PLATFORM_ADMIN_TOKEN_TYPE
from app.db.base import get_db
from app.db.tenant_context import set_tenant
from app.models.admin_model import Admin
from app.models.client_model import Client
from app.models.sales_rep_model import SalesRep
from app.models.tenant_model import Tenant
from app.repositories.admin_repository import AdminRepository
from app.repositories.client_repository import ClientRepository
from app.repositories.sales_rep_repository import SalesRepRepository
from app.repositories.tenant_repository import TenantRepository

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
    # Host de la tienda desde la que entra el visitante (X-Tenant-Domain). Es lo que
    # usa la página pública de cada distribuidora para identificarse.
    domain: str | None = None


def get_tenant_ref(
    x_tenant_slug: str | None = Header(default=None, alias="X-Tenant-Slug"),
    x_tenant_id: int | None = Header(default=None, alias="X-Tenant-ID"),
    x_tenant_domain: str | None = Header(default=None, alias="X-Tenant-Domain"),
) -> TenantRef:
    return TenantRef(slug=x_tenant_slug, id=x_tenant_id, domain=x_tenant_domain)


def _find_tenant_by_ref(
    db: Session,
    ref: TenantRef,
    body_slug: str | None = None,
) -> Tenant | None:
    """Busca el tenant que indica la referencia (sin atar la sesión): slug > dominio > id."""
    slug = (body_slug or ref.slug or "").strip().lower() or None

    repo = TenantRepository(db)
    if slug is not None:
        return repo.get_by_slug(slug)
    if ref.domain and ref.domain.strip():
        try:
            return repo.get_by_domain(ref.domain)
        except ValueError:
            return None  # no es un host válido: igual que "no encontrado"
    if ref.id is not None:
        return repo.get_by_id(ref.id)
    return None


def bind_tenant_from_ref(
    db: Session,
    ref: TenantRef,
    body_slug: str | None = None,
) -> Tenant:
    """
    Resuelve el tenant por slug (body > header), por dominio de la tienda
    (header X-Tenant-Domain) o por id (header) y ata la sesión. SOLO para
    endpoints sin autenticación (login, registro, catálogo público, tracking).
    """
    tenant = _find_tenant_by_ref(db, ref, body_slug)

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No se especificó o no se encontró el Tenant "
                "(header X-Tenant-Domain o X-Tenant-Slug)"
            ),
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

def get_current_platform_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    platform_cookie: str | None = Cookie(default=None, alias=settings.PLATFORM_AUTH_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> Admin:
    """
    Administrador de la plataforma (tabla admins), por cookie o Bearer.
    Solo acepta tokens type="platform_admin": un token de vendedor o de
    cliente de cualquier distribuidora NO sirve acá. No ata ningún tenant a
    la sesión (el admin de plataforma no pertenece a uno).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
    )

    token = platform_cookie or (credentials.credentials if credentials else None)
    if not token:
        raise credentials_exception

    payload = _decode_token(token)
    if payload.get("type") != PLATFORM_ADMIN_TOKEN_TYPE:
        raise credentials_exception

    try:
        admin_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise credentials_exception

    admin = AdminRepository(db).get_by_id(admin_id)
    if admin is None:
        raise credentials_exception
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El administrador está inactivo",
        )
    return admin


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

    return _resolve_catalog_viewer(token, db, credentials_exception)


def _resolve_catalog_viewer(
    token: str,
    db: Session,
    credentials_exception: HTTPException,
) -> SalesRep | Client:
    """Valida el token (staff o cliente), ata la sesión a su tenant y devuelve al usuario."""
    try:
        payload = _decode_token(token)
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception
        subject_id = int(subject)
        token_type = payload.get("type", "staff")
    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    if token_type not in ("staff", "client"):
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


def get_optional_catalog_viewer(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_cookie: str | None = Cookie(default=None, alias=settings.AUTH_COOKIE_NAME),
    client_auth_cookie: str | None = Cookie(default=None, alias=settings.CLIENT_AUTH_COOKIE_NAME),
    ref: TenantRef = Depends(get_tenant_ref),
    db: Session = Depends(get_db),
) -> SalesRep | Client | None:
    """
    Quién mira el catálogo de la tienda — sin exigir login.

    - Con un token válido (vendedor o cliente) manda el tenant del token; los headers
      X-Tenant-* no lo pueden pisar.
    - Sin token (o con uno vencido/inválido) es un VISITANTE ANÓNIMO: devuelve None y
      el tenant sale del dominio de la tienda (X-Tenant-Domain) o del slug
      (X-Tenant-Slug). Si no se puede resolver ninguno, 400.

    Un visitante ve lo mismo que un cliente: solo lo publicado. Ver `isinstance(viewer, SalesRep)`
    en las rutas: solo el personal ve el catálogo completo.
    """
    token = client_auth_cookie or auth_cookie
    if not token and credentials is not None:
        token = credentials.credentials

    if token:
        try:
            viewer = _resolve_catalog_viewer(
                token,
                db,
                HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"),
            )
        except HTTPException:
            viewer = None  # token vencido / de otro tipo: se lo trata como visitante

        if viewer is not None:
            # Un token válido manda: su tenant gana y los headers X-Tenant-* se ignoran
            # (igual que en el resto de los endpoints autenticados).
            return viewer

    bind_tenant_from_ref(db, ref)
    return None
