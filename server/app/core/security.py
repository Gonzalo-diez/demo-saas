from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from app.core.config import get_settings

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

    if token_type != "platform_admin" and tenant_id is None:
        raise ValueError(
            "Los tokens de tenant requieren tenant_id"
        )

    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=settings.JWT_EXPIRES_MIN
        )
    )

    payload = {
        "sub": subject,
        "type": token_type,
        "exp": expire,
    }

    if tenant_id is not None:
        payload["tenant_id"] = int(tenant_id)

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALG,
    )