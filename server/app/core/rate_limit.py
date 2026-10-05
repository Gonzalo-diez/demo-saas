from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.core.config import settings


def client_ip(request: Request) -> str:
    """
    IP con la que se cuenta el límite de requests.

    Si el frontend (Next) o un reverse proxy reenvía `/api` al backend, la IP de conexión es
    la del proxy para TODOS los usuarios y compartirían un mismo cupo (ej. 5 logins por
    minuto en toda la plataforma). Con TRUSTED_PROXY_HOPS = N se toma la IP real de
    `X-Forwarded-For`: la N-ésima desde la derecha, o sea la que agregó TU proxy de
    confianza. Los valores de la izquierda los puede inventar el cliente, por eso no se usan.
    Con 0 (por defecto) se usa la IP de conexión.
    """
    hops = settings.TRUSTED_PROXY_HOPS
    if hops > 0:
        forwarded = request.headers.get("x-forwarded-for", "")
        parts = [part.strip() for part in forwarded.split(",") if part.strip()]
        if len(parts) >= hops:
            return parts[-hops]
    return get_remote_address(request)


limiter = Limiter(key_func=client_ip, enabled=settings.RATE_LIMIT_ENABLED)
