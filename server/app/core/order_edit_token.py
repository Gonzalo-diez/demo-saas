"""
Tokens de "edición de pedido por el cliente".

Un cliente que compró por WhatsApp/la web recibe un link con uno de
estos tokens para poder agregar/quitar productos de SU pedido, sin
tener que loguearse como lo hace un sales rep.

El token:
- Está firmado con el mismo JWT_SECRET que el resto de la app (no se
  puede falsificar sin la clave del servidor).
- Tiene un "typ" propio ("order_edit") para que nunca se pueda
  confundir con un token de sesión de sales rep, ni usarse para nada
  que no sea editar ese pedido puntual.
- Está atado a un order_id específico: no sirve para tocar otros
  pedidos del mismo cliente.
- Vence solo (por defecto a las 48hs), así un link viejo no queda
  utilizable para siempre.
"""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()

TOKEN_TYPE = "order_edit"
DEFAULT_EXPIRATION_HOURS = 48

def create_order_edit_token(
    order_id: int,
    tenant_id: int,
    hours_valid: int = DEFAULT_EXPIRATION_HOURS,
) -> str:
    """
    El token también lleva el tenant del pedido: el link es público (sin login),
    así que es lo único que permite saber a qué distribuidora pertenece.
    """
    payload = {
        "sub": str(order_id),
        "typ": TOKEN_TYPE,
        "tenant_id": int(tenant_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=hours_valid),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def get_order_edit_token_tenant_id(token: str, expected_order_id: int) -> int | None:
    """
    Devuelve el tenant_id del token solo si es válido, no venció, es del tipo
    correcto y corresponde exactamente a expected_order_id. Si no, None.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except JWTError:
        return None

    if payload.get("typ") != TOKEN_TYPE:
        return None

    try:
        token_order_id = int(payload.get("sub", ""))
        tenant_id = int(payload.get("tenant_id"))
    except (TypeError, ValueError):
        return None

    if token_order_id != expected_order_id:
        return None

    return tenant_id


def verify_order_edit_token(token: str, expected_order_id: int) -> bool:
    return get_order_edit_token_tenant_id(token, expected_order_id) is not None
