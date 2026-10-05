from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from app.core.config import get_settings

PLATFORM_ADMIN_TOKEN_TYPE = "platform_admin"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(
    subject: str,
    token_type: str = "staff",
    tenant_id: int | None = None,
) -> str:
    """
    token_type distingue quién es el dueño del token: "staff" (SalesRep,
    el panel interno) o "client" (comercio B2B logueado en el catálogo).
    Es fundamental para que un id numérico de un lado no se confunda con
    el id de una tabla distinta del otro lado.

    tenant_id es OBLIGATORIO para "staff" y "client": el tenant de cada request
    se toma de este claim firmado (nunca de un header que pueda mandar el
    cliente), así un usuario de la distribuidora A no puede operar sobre la B.

    "platform_admin" (administrador de la plataforma) NO pertenece a ningún
    tenant: su token no lleva tenant_id, y por eso no sirve en ninguna ruta
    de distribuidora (esas exigen el claim).
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRES_MIN)

    payload = {
        "sub": subject,
        "type": token_type,
        "exp": expire,
    }

    if token_type == PLATFORM_ADMIN_TOKEN_TYPE:
        if tenant_id is not None:
            raise ValueError("Un token platform_admin no puede llevar tenant_id")
    else:
        if tenant_id is None:
            raise ValueError("create_access_token requiere tenant_id")
        payload["tenant_id"] = int(tenant_id)

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
