"""
Tests de integración: query `catalog_only` y endpoint /products/categories.
"""
import pytest


def _payload(**overrides):
    base = {
        "name": "Producto",
        "brand": "Marca",
        "category": "pilas",
        "unit_cost": "100.00",
        "unit_price": "150.00",
        "sku": "SKU-1",
        "stock_current": 0,
        "stock_min": 0,
        "image_url": "https://example.com/i.jpg",
    }
    base.update(overrides)
    return base


@pytest.fixture()
def seeded(client, auth_headers):
    """Un producto de catálogo y dos de categoría libre (una repetida por mayúsculas)."""
    for payload in (
        _payload(name="Pila AA", sku="P-1", category="pilas"),
        _payload(name="Yerba", sku="F-1", category="Almacén", image_url=None),
        _payload(name="Azúcar", sku="F-2", category="almacen", image_url=None),
        _payload(name="Jabón", sku="F-3", category="Limpieza", image_url=None),
    ):
        resp = client.post("/api/products/", json=payload, headers=auth_headers)
        assert resp.status_code == 201, resp.text


class TestCatalogOnlyQuery:
    def test_salesrep_sees_everything_by_default(self, client, auth_headers, seeded):
        resp = client.get("/api/products/?page_size=100", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 4

    def test_salesrep_can_preview_catalog_only(self, client, auth_headers, seeded):
        resp = client.get("/api/products/?catalog_only=true", headers=auth_headers)
        assert resp.json()["total"] == 1

    def test_client_cannot_bypass_catalog_only(self, client, client_auth_headers, seeded):
        for qs in ("", "?catalog_only=false"):
            resp = client.get(f"/api/products/{qs}", headers=client_auth_headers)
            assert resp.status_code == 200
            names = {p["name"] for p in resp.json()["items"]}
            assert names == {"Pila AA"}, f"qs={qs!r} filtró productos libres"


class TestProductCategoriesEndpoint:
    def test_requires_staff_auth(self, client, client_auth_headers):
        assert client.get("/api/products/categories").status_code in (401, 403)
        resp = client.get("/api/products/categories", headers=client_auth_headers)
        assert resp.status_code in (401, 403)

    def test_returns_catalog_free_and_aliases(self, client, auth_headers, seeded):
        resp = client.get("/api/products/categories", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()

        catalog_values = {c["value"] for c in data["catalog"]}
        assert "pilas" in catalog_values
        assert "sin clasificar" not in catalog_values

        # libres deduplicadas por normalización y sin las de catálogo
        assert sorted(data["free"], key=str.casefold) == ["Almacén", "Limpieza"] or \
            sorted(data["free"], key=str.casefold) == ["almacen", "Limpieza"]
        assert len(data["free"]) == 2
        assert "pilas" not in [c.lower() for c in data["free"]]

        assert data["catalog_aliases"]["baterias"] == "pilas"
        assert "sin clasificar" not in data["catalog_aliases"]

    def test_not_shadowed_by_product_id_route(self, client, auth_headers):
        # si "categories" cayera en /{product_id} daría 422
        assert client.get("/api/products/categories", headers=auth_headers).status_code == 200
