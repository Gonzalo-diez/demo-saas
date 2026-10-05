"""
CORS con dominios de tienda dinámicos.

Cada distribuidora entra con su propio dominio (tenants.domain). Si la tienda
llama a la API desde el navegador sin proxy, ese origen tiene que estar permitido:
además de la lista fija CORS_ORIGINS se aceptan los orígenes cuyo host sea el
dominio de una distribuidora ACTIVA.

La lista de dominios se cachea unos segundos (CORS corre en cada request, no
puede consultar la base cada vez). El alta/cambio de un tenant la invalida.
"""
from __future__ import annotations

import threading
import time
from urllib.parse import urlsplit

from sqlalchemy import select
from starlette.middleware.cors import CORSMiddleware

from app.db.tenant_context import unscoped
from app.utils.domain import domain_candidates

_TTL_SECONDS = 60.0

_lock = threading.Lock()
_cache: dict[str, object] = {"expires": 0.0, "domains": frozenset()}


def invalidate_tenant_domains_cache() -> None:
    with _lock:
        _cache["expires"] = 0.0


def _load_active_domains() -> frozenset[str]:
    # Import tardío: evita ciclos al importar app.main.
    from app.db.session import SessionLocal
    from app.models.tenant_model import Tenant

    db = SessionLocal()
    try:
        with unscoped(db):
            rows = db.scalars(select(Tenant.domain).where(Tenant.is_active.is_(True))).all()
        return frozenset(d for d in rows if d)
    finally:
        db.close()


def get_active_tenant_domains() -> frozenset[str]:
    now = time.monotonic()
    with _lock:
        if now < float(_cache["expires"]):
            return _cache["domains"]  # type: ignore[return-value]

    try:
        domains = _load_active_domains()
    except Exception:
        # Sin base (arranque, migraciones pendientes): seguimos con lo último conocido.
        domains = _cache["domains"]  # type: ignore[assignment]

    with _lock:
        _cache["domains"] = domains
        _cache["expires"] = now + _TTL_SECONDS
    return domains  # type: ignore[return-value]


class TenantAwareCORSMiddleware(CORSMiddleware):
    """CORSMiddleware que además permite el origen de la tienda de cada distribuidora."""

    def is_allowed_origin(self, origin: str) -> bool:
        if super().is_allowed_origin(origin):
            return True

        try:
            parts = urlsplit(origin)
            if parts.scheme not in ("http", "https") or not parts.hostname:
                return False
            candidates = domain_candidates(parts.hostname)  # exacto y con/sin "www."
        except ValueError:
            return False

        domains = get_active_tenant_domains()
        return any(candidate in domains for candidate in candidates)
