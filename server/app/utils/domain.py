"""
Normalización de dominios / URLs de la página (tienda) de una distribuidora.

Cada tenant tiene un `domain`: el host con el que sus clientes entran a la tienda
(ej. "tienda.distri-norte.com" o, en desarrollo, "distri-norte.localhost").
Se acepta tanto un dominio como una URL completa y se guarda SOLO el host:
sin esquema, sin puerto, sin path, en minúsculas.
"""
from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlsplit

_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_MAX_HOST_LEN = 253


def normalize_domain(value: str) -> str:
    """
    "https://Tienda.Distri-Norte.com:8443/catalogo?x=1" -> "tienda.distri-norte.com"

    Lanza ValueError (con mensaje para el usuario) si no es un host válido.
    """
    if value is None or not str(value).strip():
        raise ValueError("El dominio o URL de la tienda es obligatorio")

    raw = str(value).strip().lower()
    # urlsplit solo separa el host si hay "//": se lo agregamos cuando falta el esquema.
    if "://" not in raw:
        raw = f"//{raw}"

    try:
        host = urlsplit(raw).hostname  # ya quita esquema, credenciales, puerto, path y query
    except ValueError:
        host = None

    host = (host or "").rstrip(".")
    if not host:
        raise ValueError("El dominio o URL de la tienda no es válido (ej: tienda.midistribuidora.com)")

    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError("Usá un dominio (ej: tienda.midistribuidora.com), no una dirección IP")

    if len(host) > _MAX_HOST_LEN or not all(_LABEL_RE.match(label) for label in host.split(".")):
        raise ValueError(
            "El dominio solo puede tener letras, números, guiones y puntos "
            "(ej: tienda.midistribuidora.com)"
        )

    return host


def domain_candidates(host: str) -> list[str]:
    """
    Formas equivalentes de un host para buscarlo: el exacto primero y después con/sin
    "www." (para que `www.tienda.com` y `tienda.com` lleguen a la misma distribuidora).
    """
    host = normalize_domain(host)
    alternate = host[4:] if host.startswith("www.") else f"www.{host}"
    return [host, alternate]
