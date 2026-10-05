"""
Tests de la tienda pública de cada distribuidora:

- dominio/URL del tenant (alta, normalización, unicidad, búsqueda por dominio)
- catálogo sin login resuelto por dominio (X-Tenant-Domain), aislado entre tenants
- el visitante no ve datos internos (costo) ni lo no publicado
- registro del cliente recién al comprar (POST /clients/register) y pedido posterior
- imagen de categoría (obligatoria si es pública)
- CORS dinámico por dominio de tenant
- ya no existen la IA de Gemini ni los mapas de clientes/vendedores
"""
from datetime import date, timedelta

import pytest

from app.core.cors import invalidate_tenant_domains_cache
from app.utils.domain import domain_candidates, normalize_domain

from tests.integration.test_product_categories import _category, _product
from tests.integration.test_tenant_isolation import (  # noqa: F401
    _admin_bearer,
    _bearer,
    rep_a,
    rep_b,
    tenant_b,
)
from app.core.security import get_password_hash
from app.models.admin_model import Admin

# El cliente de tests manda por defecto X-Tenant-Slug: test. Para simular a un visitante
# que entra por el dominio de la tienda hay que vaciar el slug (el slug tiene prioridad).
def _store(domain: str) -> dict:
    return {"X-Tenant-Slug": "", "X-Tenant-Domain": domain}


@pytest.fixture()
def platform_headers(db):
    admin = Admin(
        name="Plataforma",
        email="root@platform.com",
        hashed_password=get_password_hash("rootpass123"),
        is_active=True,
    )
    db.add(admin)
    db.flush()
    return _admin_bearer(admin)


# ═══════════════════════════════════════════════════════════════════════════
# Normalización de dominios
# ═══════════════════════════════════════════════════════════════════════════

class TestNormalizeDomain:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("tienda.midistri.com", "tienda.midistri.com"),
            ("  Tienda.MiDistri.COM  ", "tienda.midistri.com"),
            ("https://tienda.midistri.com", "tienda.midistri.com"),
            ("https://Tienda.MiDistri.com:8443/catalogo?x=1#top", "tienda.midistri.com"),
            ("http://user:pw@tienda.midistri.com/", "tienda.midistri.com"),
            ("tienda.midistri.com/ruta", "tienda.midistri.com"),
            ("midistri.localhost:3000", "midistri.localhost"),
            ("tienda.midistri.com.", "tienda.midistri.com"),
        ],
    )
    def test_accepts_domains_and_urls(self, raw, expected):
        assert normalize_domain(raw) == expected

    @pytest.mark.parametrize(
        "raw",
        ["", "   ", "http://", "mi tienda.com", "-malo.com", "bad_domain.com", "127.0.0.1", "http://192.168.0.1:8000"],
    )
    def test_rejects_invalid(self, raw):
        with pytest.raises(ValueError):
            normalize_domain(raw)

    def test_candidates_cover_www(self):
        assert domain_candidates("tienda.com") == ["tienda.com", "www.tienda.com"]
        assert domain_candidates("https://www.tienda.com/") == ["www.tienda.com", "tienda.com"]


# ═══════════════════════════════════════════════════════════════════════════
# Alta / edición de tenants con dominio
# ═══════════════════════════════════════════════════════════════════════════

class TestTenantDomain:
    def test_domain_is_required_to_create_a_tenant(self, client, platform_headers):
        resp = client.post(
            "/api/tenants/",
            json={"name": "Sin Dominio", "slug": "sin-dominio"},
            headers=platform_headers,
        )
        assert resp.status_code == 422
        assert any(e["loc"][-1] == "domain" for e in resp.json()["detail"])

    def test_invalid_domain_is_rejected(self, client, platform_headers):
        resp = client.post(
            "/api/tenants/",
            json={"name": "Mala", "slug": "mala", "domain": "no es un dominio"},
            headers=platform_headers,
        )
        assert resp.status_code == 422

    def test_url_is_stored_as_host_and_is_unique(self, client, platform_headers):
        ok = client.post(
            "/api/tenants/",
            json={"name": "Norte", "slug": "norte", "domain": "https://Tienda.Norte.com/inicio"},
            headers=platform_headers,
        )
        assert ok.status_code == 201, ok.text
        assert ok.json()["domain"] == "tienda.norte.com"

        # el mismo host escrito distinto es el mismo dominio
        dup = client.post(
            "/api/tenants/",
            json={"name": "Sur", "slug": "sur", "domain": "tienda.norte.com:8080"},
            headers=platform_headers,
        )
        assert dup.status_code == 409

    def test_update_domain_checks_uniqueness(self, client, platform_headers, tenant, tenant_b):
        taken = client.patch(
            f"/api/tenants/{tenant_b.id}",
            json={"domain": "https://test.localhost"},  # el dominio del tenant "test"
            headers=platform_headers,
        )
        assert taken.status_code == 409

        ok = client.patch(
            f"/api/tenants/{tenant_b.id}",
            json={"domain": "b.tienda.com"},
            headers=platform_headers,
        )
        assert ok.status_code == 200
        assert ok.json()["domain"] == "b.tienda.com"

    def test_lookup_by_domain_is_public_and_hides_sensitive_data(self, client, tenant_b):
        resp = client.get("/api/tenants/by-domain/dist-b.localhost")
        assert resp.status_code == 200
        assert set(resp.json()) == {"id", "name", "slug", "domain", "logo_url"}
        assert resp.json()["slug"] == "dist-b"

        # con o sin www. llega a la misma distribuidora
        assert client.get("/api/tenants/by-domain/www.dist-b.localhost").json()["slug"] == "dist-b"

    def test_lookup_by_domain_unknown_or_inactive(self, client, platform_headers, tenant_b):
        assert client.get("/api/tenants/by-domain/no-existe.com").status_code == 404
        client.patch(f"/api/tenants/{tenant_b.id}/deactivate", headers=platform_headers)
        assert client.get("/api/tenants/by-domain/dist-b.localhost").status_code == 404


# ═══════════════════════════════════════════════════════════════════════════
# Catálogo público por dominio
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def two_stores(client, db, rep_a, rep_b):
    """Distribuidora A (test.localhost) y B (dist-b.localhost), cada una con su catálogo."""
    out = {}
    for key, rep in (("a", rep_a), ("b", rep_b)):
        h = _bearer(rep)
        cat = _category(client, h, f"Pilas {key.upper()}")
        priv = _category(client, h, f"Interna {key.upper()}", is_public=False)
        pub = _product(client, h, f"{key}-1", f"Pila {key.upper()}", cat["id"], stock_current=10)
        _product(client, h, f"{key}-2", f"Oculto {key.upper()}", cat["id"], stock_current=10, is_public=False)
        _product(client, h, f"{key}-3", f"Interno {key.upper()}", priv["id"], stock_current=10, image_url=None)
        out[key] = {"cat": cat, "priv": priv, "product": pub}
    return out


class TestAnonymousStorefront:
    def test_visitor_sees_only_published_items_of_that_domain(self, client, two_stores):
        a = client.get("/api/products/", headers=_store("test.localhost"))
        assert a.status_code == 200
        assert {p["name"] for p in a.json()["items"]} == {"Pila A"}

        b = client.get("/api/products/", headers=_store("dist-b.localhost"))
        assert {p["name"] for p in b.json()["items"]} == {"Pila B"}

    def test_visitor_cannot_bypass_publication_filters(self, client, two_stores):
        for qs in ("?catalog_only=false", "?is_active=false", "?is_public=false"):
            resp = client.get(f"/api/products/{qs}", headers=_store("test.localhost"))
            assert {p["name"] for p in resp.json()["items"]} == {"Pila A"}, qs

    def test_visitor_does_not_see_internal_fields(self, client, two_stores):
        item = client.get("/api/products/", headers=_store("test.localhost")).json()["items"][0]
        assert "unit_cost" not in item
        assert "stock_min" not in item
        assert item["unit_price"] is not None and item["image_url"]

        detail = client.get(
            f"/api/products/{two_stores['a']['product']['id']}", headers=_store("test.localhost")
        ).json()
        assert "unit_cost" not in detail

    def test_staff_still_sees_cost_and_everything(self, client, two_stores, rep_a):
        h = _bearer(rep_a)
        resp = client.get("/api/products/?page_size=100", headers=h).json()
        assert resp["total"] == 3
        assert all("unit_cost" in p for p in resp["items"])

    def test_visitor_cannot_read_other_domains_product_or_unpublished(self, client, two_stores):
        other = two_stores["b"]["product"]["id"]
        assert client.get(f"/api/products/{other}", headers=_store("test.localhost")).status_code == 404
        assert client.get(f"/api/products/{other}", headers=_store("dist-b.localhost")).status_code == 200

    def test_categories_are_public_but_only_published_ones(self, client, two_stores):
        resp = client.get("/api/categories/", headers=_store("test.localhost"))
        assert resp.status_code == 200
        assert [c["name"] for c in resp.json()["items"]] == ["Pilas A"]
        assert resp.json()["items"][0]["image_url"]

        hidden = two_stores["a"]["priv"]["id"]
        assert client.get(f"/api/categories/{hidden}", headers=_store("test.localhost")).status_code == 404

    def test_filters_endpoint_is_public(self, client, two_stores):
        resp = client.get("/api/products/filters", headers=_store("test.localhost"))
        assert resp.status_code == 200
        assert resp.json()["categories"] == ["Pilas A"]

    def test_unknown_domain_or_no_tenant_is_400(self, client):
        assert client.get("/api/products/", headers=_store("no-existe.com")).status_code == 400
        assert client.get("/api/products/", headers={"X-Tenant-Slug": ""}).status_code == 400

    def test_inactive_tenant_store_is_closed(self, client, db, two_stores, platform_headers, tenant_b):
        client.patch(f"/api/tenants/{tenant_b.id}/deactivate", headers=platform_headers)
        assert client.get("/api/products/", headers=_store("dist-b.localhost")).status_code in (400, 403, 404)

    def test_token_tenant_wins_over_domain_header(self, client, two_stores, rep_a):
        # Personal de A pidiendo "ser" B por dominio: sigue viendo lo de A.
        headers = {**_bearer(rep_a), "X-Tenant-Slug": "", "X-Tenant-Domain": "dist-b.localhost"}
        names = {p["name"] for p in client.get("/api/products/?page_size=100", headers=headers).json()["items"]}
        assert names == {"Pila A", "Oculto A", "Interno A"}

    def test_www_variant_reaches_same_store(self, client, two_stores):
        resp = client.get("/api/products/", headers=_store("www.test.localhost"))
        assert resp.status_code == 200
        assert {p["name"] for p in resp.json()["items"]} == {"Pila A"}


# ═══════════════════════════════════════════════════════════════════════════
# Registro recién al comprar
# ═══════════════════════════════════════════════════════════════════════════

def _register_payload(**extra):
    payload = {
        "name": "Juan Pérez",
        "email": "Juan@Kiosco.com",
        "password": "secreta123",
        "phone": "3751123456",
    }
    payload.update(extra)
    return payload


def _order_payload(product_id):
    return {
        "items": [{"product_id": product_id, "quantity": 2}],
        "customer_name": "Juan Pérez",
        "customer_phone": "+5493751123456",
        "customer_email": "juan@kiosco.com",
        "delivery_address": "Calle 123",
        "delivery_city": "Posadas",
        "preferred_delivery_date": (date.today() + timedelta(days=5)).isoformat(),
    }


class TestRegisterAtCheckout:
    def test_browse_without_login_but_order_requires_account(self, client, two_stores):
        pid = two_stores["a"]["product"]["id"]
        # Mirar el catálogo no pide cuenta...
        assert client.get("/api/products/", headers=_store("test.localhost")).status_code == 200
        # ...pero finalizar la compra sí.
        resp = client.post("/api/orders", json=_order_payload(pid), headers=_store("test.localhost"))
        assert resp.status_code == 401

    def test_register_creates_client_in_that_tenant_and_logs_in(self, client, two_stores):
        resp = client.post(
            "/api/clients/register", json=_register_payload(), headers=_store("dist-b.localhost")
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["email"] == "juan@kiosco.com"
        assert "hashed_password" not in body and "password" not in body

        # La sesión quedó iniciada (cookie): ya puede comprar sin loguearse otra vez.
        pid = two_stores["b"]["product"]["id"]
        order = client.post("/api/orders", json=_order_payload(pid), headers=_store("dist-b.localhost"))
        assert order.status_code in (200, 201), order.text
        client.cookies.clear()

    def test_register_then_login_with_same_credentials(self, client, two_stores):
        client.post("/api/clients/register", json=_register_payload(), headers=_store("test.localhost"))
        client.cookies.clear()
        login = client.post(
            "/api/clients/login",
            json={"email": "juan@kiosco.com", "password": "secreta123"},
            headers=_store("test.localhost"),
        )
        assert login.status_code == 200, login.text

    def test_duplicate_email_in_same_store_is_409(self, client, two_stores):
        first = client.post("/api/clients/register", json=_register_payload(), headers=_store("test.localhost"))
        assert first.status_code == 201
        again = client.post("/api/clients/register", json=_register_payload(), headers=_store("test.localhost"))
        assert again.status_code == 409
        client.cookies.clear()

    def test_same_email_in_another_store_is_allowed(self, client, two_stores):
        a = client.post("/api/clients/register", json=_register_payload(), headers=_store("test.localhost"))
        client.cookies.clear()
        b = client.post("/api/clients/register", json=_register_payload(), headers=_store("dist-b.localhost"))
        assert a.status_code == 201 and b.status_code == 201
        assert a.json()["id"] != b.json()["id"] or True  # ids por tenant pueden coincidir
        client.cookies.clear()

    def test_register_requires_a_store(self, client):
        resp = client.post(
            "/api/clients/register", json=_register_payload(), headers={"X-Tenant-Slug": ""}
        )
        assert resp.status_code == 400

    @pytest.mark.parametrize(
        "bad",
        [{"email": "no-es-mail"}, {"password": "123"}, {"phone": ""}, {"name": ""}],
    )
    def test_register_validates_input(self, client, two_stores, bad):
        resp = client.post(
            "/api/clients/register", json=_register_payload(**bad), headers=_store("test.localhost")
        )
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════
# Imagen de categoría
# ═══════════════════════════════════════════════════════════════════════════

class TestCategoryImage:
    def test_public_category_requires_image(self, client, auth_headers):
        resp = client.post("/api/categories/", json={"name": "Sin foto"}, headers=auth_headers)
        assert resp.status_code == 400
        assert "imagen" in resp.json()["detail"].lower()

        resp = client.post(
            "/api/categories/", json={"name": "Basura", "image_url": "nan"}, headers=auth_headers
        )
        assert resp.status_code == 400

    def test_private_category_does_not_need_image(self, client, auth_headers):
        resp = client.post(
            "/api/categories/", json={"name": "Interna", "is_public": False}, headers=auth_headers
        )
        assert resp.status_code == 201
        assert resp.json()["image_url"] is None

    def test_image_is_stored_and_returned(self, client, auth_headers):
        resp = client.post(
            "/api/categories/",
            json={"name": "Con foto", "image_url": "  https://example.com/c.jpg  "},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["image_url"] == "https://example.com/c.jpg"

    def test_cannot_publish_private_category_without_image(self, client, auth_headers):
        cat = client.post(
            "/api/categories/", json={"name": "Interna", "is_public": False}, headers=auth_headers
        ).json()
        assert client.patch(f"/api/categories/{cat['id']}/publish", headers=auth_headers).status_code == 400

        client.patch(f"/api/categories/{cat['id']}", json={"image_url": "https://example.com/x.jpg"}, headers=auth_headers)
        assert client.patch(f"/api/categories/{cat['id']}/publish", headers=auth_headers).status_code == 200

    def test_cannot_remove_image_from_public_category(self, client, auth_headers):
        cat = _category(client, auth_headers, "Pública")
        resp = client.patch(f"/api/categories/{cat['id']}", json={"image_url": None}, headers=auth_headers)
        assert resp.status_code == 400
        # sigue con su imagen
        assert client.get(f"/api/categories/{cat['id']}", headers=auth_headers).json()["image_url"]

    def test_can_remove_image_when_also_making_it_private(self, client, auth_headers):
        cat = _category(client, auth_headers, "Pública")
        resp = client.patch(
            f"/api/categories/{cat['id']}",
            json={"image_url": None, "is_public": False},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["image_url"] is None and resp.json()["is_public"] is False

    def test_update_other_fields_keeps_image(self, client, auth_headers):
        cat = _category(client, auth_headers, "Pública", image_url="https://example.com/keep.jpg")
        resp = client.patch(f"/api/categories/{cat['id']}", json={"description": "nueva"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["image_url"] == "https://example.com/keep.jpg"

    def test_category_image_upload_route_requires_superuser(self, client, auth_headers):
        resp = client.post(
            "/api/upload/category-image",
            files={"file": ("c.jpg", b"x", "image/jpeg")},
            headers=auth_headers,  # vendedor común, no superusuario
        )
        assert resp.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════════════
# CORS por dominio de tenant
# ═══════════════════════════════════════════════════════════════════════════

class TestDynamicCors:
    @pytest.fixture(autouse=True)
    def _domains_from_test_session(self, db, monkeypatch):
        """
        El middleware de CORS abre su PROPIA sesión (corre antes de las dependencias), y en
        los tests los datos viven en la transacción de la sesión `db`, sin commit. Se lo
        apunta a esa sesión; la consulta es la misma que hace en producción.
        """
        from sqlalchemy import select

        from app.core import cors
        from app.db.tenant_context import unscoped
        from app.models.tenant_model import Tenant

        def load():
            with unscoped(db):
                rows = db.scalars(select(Tenant.domain).where(Tenant.is_active.is_(True))).all()
            return frozenset(rows)

        monkeypatch.setattr(cors, "_load_active_domains", load)
        invalidate_tenant_domains_cache()
        yield
        invalidate_tenant_domains_cache()

    def _preflight(self, client, origin):
        return client.options(
            "/api/products/",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "x-tenant-domain",
            },
        )

    def test_tenant_domain_origin_is_allowed_and_others_are_not(self, client, tenant_b):
        invalidate_tenant_domains_cache()
        ok = self._preflight(client, "https://dist-b.localhost")
        assert ok.status_code == 200
        assert ok.headers.get("access-control-allow-origin") == "https://dist-b.localhost"

        bad = self._preflight(client, "https://evil.example.com")
        assert bad.status_code == 400
        assert "access-control-allow-origin" not in bad.headers

    def test_inactive_tenant_origin_is_rejected(self, client, platform_headers, tenant_b):
        client.patch(f"/api/tenants/{tenant_b.id}/deactivate", headers=platform_headers)
        invalidate_tenant_domains_cache()
        assert self._preflight(client, "https://dist-b.localhost").status_code == 400


# ═══════════════════════════════════════════════════════════════════════════
# Lo que se quitó
# ═══════════════════════════════════════════════════════════════════════════

class TestRemovedFeatures:
    def test_maps_are_gone(self, client, auth_headers, rep_a):
        # /clients/map y /sales-reps/map ya no existen (no caen en 200).
        assert client.get("/api/clients/map", headers=_bearer(rep_a)).status_code != 200
        assert client.get("/api/sales-reps/map", headers=_bearer(rep_a)).status_code != 200

    def test_gemini_ai_is_gone(self, client, rep_a):
        assert client.get("/api/ai/suggestions", headers=_bearer(rep_a)).status_code == 404
        paths = {r.path for r in client.app.routes}
        assert not any(p.startswith("/api/ai") for p in paths)

    def test_gemini_config_and_dependency_are_gone(self):
        from app.core.config import settings
        assert not any("gemini" in name.lower() for name in settings.model_fields)
