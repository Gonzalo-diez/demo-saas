"""
Tests de integración: categorías propias de cada distribuidora y publicación
(público / no público) de categorías y productos.

Reglas:
- Un cliente (tienda online) solo ve productos ACTIVOS y PÚBLICOS cuya categoría
  (si tienen) también es PÚBLICA.
- El personal ve todo; catalog_only=true le sirve para previsualizar el catálogo.
- Una categoría que se crea sola al importar nace PRIVADA.
"""
import pytest

# Fixtures de dos distribuidoras (definidas en test_tenant_isolation.py)
from tests.integration.test_tenant_isolation import rep_a, rep_b, tenant_b  # noqa: F401


def _category(client, headers, name, **extra):
    payload = {"name": name, **extra}
    # Una categoría pública necesita imagen (igual que un producto): el helper se la
    # pone salvo que el test pida una privada o maneje image_url por su cuenta.
    if payload.get("is_public", True) and "image_url" not in payload:
        payload["image_url"] = "https://example.com/cat.jpg"
    resp = client.post("/api/categories/", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _product(client, headers, sku, name, category_id=None, **extra):
    payload = {
        "name": name,
        "brand": "Marca",
        "category_id": category_id,
        "unit_cost": "100.00",
        "unit_price": "150.00",
        "sku": sku,
        "stock_current": 0,
        "stock_min": 0,
        "image_url": "https://example.com/i.jpg",
    }
    payload.update(extra)
    resp = client.post("/api/products/", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def seeded(client, auth_headers):
    """Una categoría pública, una privada, y productos en cada una (+ uno despublicado)."""
    pub = _category(client, auth_headers, "Pilas")
    priv = _category(client, auth_headers, "Insumos internos", is_public=False)
    _product(client, auth_headers, "P-1", "Pila AA", pub["id"])
    _product(client, auth_headers, "P-2", "Pila AAA (despublicada)", pub["id"], is_public=False)
    _product(client, auth_headers, "I-1", "Insumo", priv["id"], image_url=None)
    return {"pub": pub, "priv": priv}


class TestCategoryCrud:
    def test_create_defaults_to_public(self, client, auth_headers):
        cat = _category(client, auth_headers, "  Golosinas  ")
        assert cat["name"] == "Golosinas"
        assert cat["slug"] == "golosinas"
        assert cat["is_public"] is True
        assert cat["requires_age_verification"] is False

    def test_names_are_unique_ignoring_case_and_accents(self, client, auth_headers):
        _category(client, auth_headers, "Almacén")
        resp = client.post("/api/categories/", json={"name": "almacen"}, headers=auth_headers)
        assert resp.status_code == 409

    def test_reserved_placeholder_name_rejected(self, client, auth_headers):
        resp = client.post("/api/categories/", json={"name": "Sin Clasificar"}, headers=auth_headers)
        assert resp.status_code == 400

    def test_requires_staff_login(self, client, client_auth_headers):
        assert client.post("/api/categories/", json={"name": "X"}).status_code == 401
        resp = client.post("/api/categories/", json={"name": "X"}, headers=client_auth_headers)
        assert resp.status_code in (401, 403)

    def test_update_publish_unpublish(self, client, auth_headers):
        cat = _category(client, auth_headers, "Bebidas")
        off = client.patch(f"/api/categories/{cat['id']}/unpublish", headers=auth_headers)
        assert off.status_code == 200 and off.json()["is_public"] is False
        on = client.patch(f"/api/categories/{cat['id']}/publish", headers=auth_headers)
        assert on.json()["is_public"] is True
        upd = client.patch(
            f"/api/categories/{cat['id']}",
            json={"description": "Gaseosas y aguas", "requires_age_verification": True},
            headers=auth_headers,
        )
        assert upd.json()["description"] == "Gaseosas y aguas"
        assert upd.json()["requires_age_verification"] is True

    def test_rename_updates_products_copy_of_the_name(self, client, auth_headers):
        cat = _category(client, auth_headers, "Gaseosas")
        pid = _product(client, auth_headers, "G-1", "Cola", cat["id"])["id"]
        resp = client.patch(f"/api/categories/{cat['id']}", json={"name": "Bebidas sin alcohol"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["slug"] == "bebidas-sin-alcohol"
        product = client.get(f"/api/products/{pid}", headers=auth_headers).json()
        assert product["category"] == "Bebidas sin alcohol"
        assert product["category_id"] == cat["id"]
        # y la búsqueda por texto sigue funcionando con el nombre nuevo
        found = client.get("/api/products/?search=sin alcohol", headers=auth_headers).json()
        assert found["total"] == 1

    def test_list_shows_product_count(self, client, auth_headers, seeded):
        items = {c["name"]: c for c in client.get("/api/categories/", headers=auth_headers).json()["items"]}
        assert items["Pilas"]["product_count"] == 2
        assert items["Insumos internos"]["product_count"] == 1

    def test_cannot_delete_category_with_products(self, client, auth_headers, seeded):
        resp = client.delete(f"/api/categories/{seeded['pub']['id']}", headers=auth_headers)
        assert resp.status_code == 409

    def test_can_delete_empty_category(self, client, auth_headers):
        cat = _category(client, auth_headers, "Vacía")
        assert client.delete(f"/api/categories/{cat['id']}", headers=auth_headers).status_code == 204
        assert client.get(f"/api/categories/{cat['id']}", headers=auth_headers).status_code == 404

    def test_product_with_unknown_category_id_is_404(self, client, auth_headers):
        resp = client.post(
            "/api/products/",
            json={"name": "X", "brand": "M", "category_id": 99999, "unit_cost": "1", "unit_price": "2",
                  "image_url": "https://example.com/i.jpg"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_legacy_category_text_reuses_or_creates_a_private_category(self, client, auth_headers):
        pub = _category(client, auth_headers, "Pilas")
        a = _product(client, auth_headers, "L-1", "Pila", category_id=None, category="pilas")
        assert a["category_id"] == pub["id"]            # reutiliza la existente (sin importar mayúsculas)
        b = _product(client, auth_headers, "L-2", "Cosa", category_id=None, category="Repuestos", image_url=None)
        cats = {c["name"]: c for c in client.get("/api/categories/", headers=auth_headers).json()["items"]}
        assert cats["Repuestos"]["is_public"] is False   # nace privada: nada se publica solo
        assert b["category_id"] == cats["Repuestos"]["id"]


class TestCatalogVisibility:
    def test_salesrep_sees_everything_by_default(self, client, auth_headers, seeded):
        resp = client.get("/api/products/?page_size=100", headers=auth_headers)
        assert resp.json()["total"] == 3

    def test_salesrep_can_preview_catalog_only(self, client, auth_headers, seeded):
        resp = client.get("/api/products/?catalog_only=true", headers=auth_headers)
        names = {p["name"] for p in resp.json()["items"]}
        assert names == {"Pila AA"}

    def test_client_only_sees_published(self, client, client_auth_headers, seeded):
        for qs in ("", "?catalog_only=false", "?is_active=false", "?is_public=false"):
            resp = client.get(f"/api/products/{qs}", headers=client_auth_headers)
            assert resp.status_code == 200
            names = {p["name"] for p in resp.json()["items"]}
            assert names == {"Pila AA"}, f"qs={qs!r} filtró productos no publicados"

    def test_client_gets_404_on_unpublished_product(self, client, auth_headers, client_auth_headers, seeded):
        items = client.get("/api/products/?page_size=100", headers=auth_headers).json()["items"]
        by_name = {p["name"]: p["id"] for p in items}
        assert client.get(f"/api/products/{by_name['Pila AA']}", headers=client_auth_headers).status_code == 200
        for hidden in ("Pila AAA (despublicada)", "Insumo"):
            resp = client.get(f"/api/products/{by_name[hidden]}", headers=client_auth_headers)
            assert resp.status_code == 404, hidden

    def test_unpublishing_a_category_hides_all_its_products(self, client, auth_headers, client_auth_headers, seeded):
        client.patch(f"/api/categories/{seeded['pub']['id']}/unpublish", headers=auth_headers)
        assert client.get("/api/products/", headers=client_auth_headers).json()["total"] == 0
        client.patch(f"/api/categories/{seeded['pub']['id']}/publish", headers=auth_headers)
        assert client.get("/api/products/", headers=client_auth_headers).json()["total"] == 1

    def test_publish_and_unpublish_a_product(self, client, auth_headers, client_auth_headers, seeded):
        items = client.get("/api/products/?page_size=100", headers=auth_headers).json()["items"]
        pid = {p["name"]: p["id"] for p in items}["Pila AAA (despublicada)"]

        on = client.patch(f"/api/products/{pid}/publish", headers=auth_headers)
        assert on.status_code == 200 and on.json()["is_public"] is True
        assert client.get("/api/products/", headers=client_auth_headers).json()["total"] == 2

        off = client.patch(f"/api/products/{pid}/unpublish", headers=auth_headers)
        assert off.json()["is_public"] is False
        assert client.get("/api/products/", headers=client_auth_headers).json()["total"] == 1

    def test_cannot_publish_product_without_image(self, client, auth_headers, seeded):
        items = client.get("/api/products/?page_size=100", headers=auth_headers).json()["items"]
        pid = {p["name"]: p["id"] for p in items}["Insumo"]   # categoría privada, sin imagen
        # en categoría privada no hay problema (no se va a ver igual)
        assert client.patch(f"/api/products/{pid}/publish", headers=auth_headers).status_code == 200
        # al hacer pública la categoría, publicarlo sí exige imagen
        client.patch(f"/api/categories/{seeded['priv']['id']}", json={"image_url": "https://example.com/c.jpg"}, headers=auth_headers)
        assert client.patch(f"/api/categories/{seeded['priv']['id']}/publish", headers=auth_headers).status_code == 200
        client.patch(f"/api/products/{pid}/unpublish", headers=auth_headers)
        assert client.patch(f"/api/products/{pid}/publish", headers=auth_headers).status_code == 400

    def test_filter_by_category_id(self, client, auth_headers, seeded):
        resp = client.get(f"/api/products/?category_id={seeded['priv']['id']}", headers=auth_headers)
        assert {p["name"] for p in resp.json()["items"]} == {"Insumo"}

    def test_filters_for_client_only_list_published_categories(self, client, client_auth_headers, seeded):
        data = client.get("/api/products/filters", headers=client_auth_headers).json()
        assert data["categories"] == ["Pilas"]

    def test_client_categories_endpoint_hides_private_ones(self, client, auth_headers, client_auth_headers, seeded):
        staff = client.get("/api/categories/", headers=auth_headers).json()
        assert {c["name"] for c in staff["items"]} == {"Pilas", "Insumos internos"}

        for qs in ("", "?is_public=false"):
            resp = client.get(f"/api/categories/{qs}", headers=client_auth_headers).json()
            assert {c["name"] for c in resp["items"]} == {"Pilas"}

        priv_id = seeded["priv"]["id"]
        assert client.get(f"/api/categories/{priv_id}", headers=client_auth_headers).status_code == 404
        assert client.get(f"/api/categories/{priv_id}", headers=auth_headers).status_code == 200

    def test_old_categories_endpoint_is_gone(self, client, auth_headers):
        # /products/categories (lista fija) se reemplazó por /categories
        assert client.get("/api/products/categories", headers=auth_headers).status_code in (404, 422)


class TestShopOrdersRespectPublication:
    def _order_body(self, pid):
        from datetime import date, timedelta
        return {
            "items": [{"product_id": pid, "quantity": 1}],
            "customer_name": "Juan Perez",
            "customer_phone": "+5493751123456",
            "customer_email": "juan@test.com",
            "delivery_address": "Calle 123",
            "delivery_city": "Posadas",
            "preferred_delivery_date": (date.today() + timedelta(days=5)).isoformat(),
        }

    def test_client_can_order_published_product(self, client, auth_headers, client_auth_headers, seeded):
        pid = {p["name"]: p["id"] for p in client.get("/api/products/?page_size=100", headers=auth_headers).json()["items"]}["Pila AA"]
        resp = client.post("/api/orders", json=self._order_body(pid), headers=client_auth_headers)
        assert resp.status_code == 201, resp.text

    @pytest.mark.parametrize("hidden", ["Pila AAA (despublicada)", "Insumo"])
    def test_client_cannot_order_unpublished_product(self, client, auth_headers, client_auth_headers, seeded, hidden):
        pid = {p["name"]: p["id"] for p in client.get("/api/products/?page_size=100", headers=auth_headers).json()["items"]}[hidden]
        resp = client.post("/api/orders", json=self._order_body(pid), headers=client_auth_headers)
        # Los errores de negocio de pedidos se reportan como 422; y no revela que existe.
        assert resp.status_code == 422, resp.text
        assert "no existe" in resp.text

    def test_age_verification_comes_from_the_category_flag(self, client, auth_headers, client_auth_headers):
        cat = _category(client, auth_headers, "Tabaco", requires_age_verification=True)
        pid = _product(client, auth_headers, "T-1", "Cigarrillos", cat["id"])["id"]
        resp = client.post("/api/orders", json=self._order_body(pid), headers=client_auth_headers)
        assert resp.status_code == 422
        assert "regulados" in resp.text

        body = {**self._order_body(pid), "customer_dni": "12345678", "age_confirmed": True}
        assert client.post("/api/orders", json=body, headers=client_auth_headers).status_code == 201


class TestCategoriesAreIsolatedPerTenant:
    def test_each_distributor_has_its_own_categories(self, client, db, tenant, rep_a, rep_b):
        from tests.integration.test_tenant_isolation import _bearer

        a = _category(client, _bearer(rep_a), "Pilas")
        b = _category(client, _bearer(rep_b), "Pilas")          # mismo nombre, otro tenant: válido
        assert a["id"] != b["id"]

        assert client.get(f"/api/categories/{a['id']}", headers=_bearer(rep_b)).status_code == 404
        assert client.patch(f"/api/categories/{a['id']}", json={"name": "X"}, headers=_bearer(rep_b)).status_code == 404
        assert client.delete(f"/api/categories/{a['id']}", headers=_bearer(rep_b)).status_code == 404
        assert client.get("/api/categories/", headers=_bearer(rep_b)).json()["total"] == 1

    def test_cannot_use_other_tenants_category_on_a_product(self, client, db, rep_a, rep_b):
        from tests.integration.test_tenant_isolation import _bearer

        cat_b = _category(client, _bearer(rep_b), "De B")
        resp = client.post(
            "/api/products/",
            json={"name": "X", "brand": "M", "category_id": cat_b["id"], "unit_cost": "1", "unit_price": "2",
                  "image_url": "https://example.com/i.jpg"},
            headers=_bearer(rep_a),
        )
        assert resp.status_code == 404
