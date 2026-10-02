from fastapi import Response
from app.core.config import settings

def set_auth_cookie(response: Response, access_token: str, cookie_name: str | None = None) -> None:
    response.set_cookie(
        key=cookie_name or settings.AUTH_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path=settings.AUTH_COOKIE_PATH,
        max_age=settings.JWT_EXPIRES_MIN * 60,
    )

def clear_auth_cookie(response: Response, cookie_name: str | None = None) -> None:
    response.delete_cookie(
        key=cookie_name or settings.AUTH_COOKIE_NAME,
        path=settings.AUTH_COOKIE_PATH,
    )