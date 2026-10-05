from __future__ import annotations
import json
from functools import lru_cache
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """App settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    ENV: str = Field(default="dev")
    PROJECT_NAME: str = Field(default="Distribuidora Choco")

    # Database
    DATABASE_URL: str

    # Auth / JWT
    JWT_SECRET: str = Field(default="change-me")
    JWT_ALG: str = Field(default="HS256")
    JWT_EXPIRES_MIN: int = Field(default=60)
    
    SQL_ECHO: bool = Field(default=False)

    # Superuser
    FIRST_SUPERUSER_EMAIL: str | None = None
    FIRST_SUPERUSER_PASSWORD: str | None = None

    # Tenant inicial (se crea al arrancar si no existe)
    FIRST_TENANT_NAME: str = Field(default="Principal")
    FIRST_TENANT_SLUG: str = Field(default="main")
    # Dominio de la tienda del tenant inicial. En desarrollo, "*.localhost" resuelve a
    # 127.0.0.1 en los navegadores, así que no hace falta tocar el archivo hosts.
    FIRST_TENANT_DOMAIN: str = Field(default="main.localhost")
    FIRST_TENANT_EMAIL: str | None = None

    # Administradores de la PLATAFORMA (alta/baja de distribuidoras).
    # Son una tabla aparte (admins) y se loguean en /api/admin/login.
    # El primero se crea al arrancar si estas dos variables están completas.
    FIRST_ADMIN_NAME: str = Field(default="Platform Admin")
    FIRST_ADMIN_EMAIL: str | None = None
    FIRST_ADMIN_PASSWORD: str | None = None

    # Cookies
    AUTH_COOKIE_NAME: str = Field(default="districhocomap_token")
    PLATFORM_AUTH_COOKIE_NAME: str = Field(default="districhocomap_platform_token")
    CLIENT_AUTH_COOKIE_NAME: str = Field(default="districhocomap_client_token")
    AUTH_COOKIE_SECURE: bool = Field(default=False)
    AUTH_COOKIE_SAMESITE: str = Field(default="lax")
    AUTH_COOKIE_PATH: str = Field(default="/")
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str | None = None
    CLOUDINARY_API_KEY: str | None = None
    CLOUDINARY_API_SECRET: str | None = None
    CLOUDINARY_FOLDER: str = Field(default="distribuidora/productos")
    
    # Resend
    RESEND_API_KEY: str | None = None
    ORDER_FROM_EMAIL: str | None = None
    ORDER_ADMIN_EMAIL: str | None = None

    # WhatsApp Cloud API
    WHATSAPP_VERIFY_TOKEN: str | None = None
    WHATSAPP_APP_SECRET: str | None = None
    WHATSAPP_ACCESS_TOKEN: str | None = None
    WHATSAPP_PHONE_NUMBER_ID: str | None = None
    WHATSAPP_BUSINESS_NAME: str = Field(default="Districhoco")
    
    # Rate limiting (slowapi). Se puede apagar para demos locales con varios usuarios.
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    # Cuántos proxies de confianza hay delante del backend (frontend que reenvía /api, nginx,
    # Cloudflare...). 0 = ninguno: el límite se cuenta por la IP de conexión. Con N > 0 se toma
    # la IP real de X-Forwarded-For (la N-ésima desde la derecha). Ver app/core/rate_limit.py.
    TRUSTED_PROXY_HOPS: int = Field(default=0, ge=0, le=5)

    # CORS
    FRONTEND_ORIGIN: str = Field(default="http://localhost:3000")

    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"])
    
    # Notificaciones (stock y cheques)
    NOTIFICATIONS_TIMEZONE: str = Field(default="America/Argentina/Buenos_Aires")
    # Margen (%) sobre el stock mínimo para avisar "cerca del mínimo"
    STOCK_NEAR_MIN_MARGIN_PERCENT: int = Field(default=20, ge=0)
    # Días de anticipación para avisar cheques por cobrar / por vencer
    CHECK_ALERT_DAYS_BEFORE: int = Field(default=3, ge=0)
    # Días que se conservan las notificaciones ya resueltas
    NOTIFICATIONS_RETENTION_DAYS: int = Field(default=60, ge=1)

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v):
        if v is None:
            return ["http://localhost:3000", "http://localhost:5173"]
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if s == "*":
                return ["*"]
            if s.startswith("["):
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        return parsed
                except Exception:
                    pass
            return [item.strip() for item in s.split(",") if item.strip()]
        return v

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()