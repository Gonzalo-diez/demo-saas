from jose import jwt, JWTError
from datetime import datetime, timezone
from app.core.redis_client import redis_client
from app.core.config import get_settings

settings = get_settings()
BLACKLIST_PREFIX = "token_blacklist:"

async def blacklist_token(token: str) -> None:
    """Agrega el token a la blacklist con TTL = tiempo restante hasta expiración."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALG],
        )
        exp = payload.get("exp")
        if exp is None:
            return

        now = int(datetime.now(timezone.utc).timestamp())
        ttl = exp - now

        if ttl > 0:
            await redis_client.setex(
                f"{BLACKLIST_PREFIX}{token}",
                ttl,
                "1",
            )
    except JWTError:
        pass  # token inválido, no hace falta blacklistearlo

async def is_token_blacklisted(token: str) -> bool:
    """Retorna True si el token fue revocado."""
    return await redis_client.exists(f"{BLACKLIST_PREFIX}{token}") == 1