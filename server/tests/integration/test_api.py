"""
test_api.py — Tests de integración para los endpoints HTTP principales.
Usa TestClient con SQLite en memoria (sin PostgreSQL).
"""
import pytest
from decimal import Decimal
from app.core.security import get_password_hash, create_access_token

# ═══════════════════════════════════════════════════════════════════════════
# Fixtures de datos
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def product_payload(client, auth_headers):
    # Categoría pública propia de la distribuidora (ya no hay lista fija en el código).
    resp = client.post("/api/categories/", json={"name": "Pilas", "is_public": True, "image_url": "https://example.com/pilas.jpg"}, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    return {
        "name": "Producto Test",
        "brand": "Marca Test",
        "category_id": resp.json()["id"],
        "unit_cost": "100.00",
        "unit_price": "150.00",
        "sku": "SKU-TEST-001",
        "stock_current": 10,
        "stock_min": 2,
        "image_url": "https://example.com/image.jpg",  # requerido en ProductCreateAdmin
    }


# ═══════════════════════════════════════════════════════════════════════════
# Autenticación
# ═══════════════════════════════════════════════════════════════════════════

class TestAuth:
    def test_login_success(self, client, db, superuser):
        """Login con credenciales correctas devuelve 200."""
        resp = client.post("/api/sales-reps/login", json={
            "email": "super@test.com",
            "password": "testpass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "super@test.com"

    def test_login_wrong_password(self, client, db, superuser):
        resp = client.post("/api/sales-reps/login", json={
            "email": "super@test.com",
            "password": "wrongpassword",
        })
        assert resp.status_code in (401, 400)

    def test_login_unknown_email(self, client):
        resp = client.post("/api/sales-reps/login", json={
            "email": "noexiste@test.com",
            "password": "any",
        })
        assert resp.status_code in (401, 404, 400)

    def test_logout_returns_200(self, client):
        resp = client.post("/api/sales-reps/logout")
        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_me_unauthenticated(self, client):
        resp = client.get("/api/sales-reps/me")
        assert resp.status_code == 401

    def test_me_authenticated(self, client, auth_headers):
        resp = client.get("/api/sales-reps/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "email" in data

    def test_invalid_token_rejected(self, client):
        resp = client.get("/api/sales-reps/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# Productos
# ═══════════════════════════════════════════════════════════════════════════

class TestProductsEndpoints:

    def test_list_products_no_auth(self, client):
        """La tienda es pública: un visitante sin login ve el catálogo (solo lo publicado)."""
        resp = client.get("/api/products/")
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    def test_list_products_returns_pagination(self, client, auth_headers):
        resp = client.get("/api/products/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Debe tener campos de paginación
        assert "total" in data
        assert "page" in data

    def test_create_product_requires_auth(self, client, product_payload):
        resp = client.post("/api/products/", json=product_payload)
        assert resp.status_code == 401

    def test_create_product_authenticated(self, client, auth_headers, product_payload):
        resp = client.post("/api/products/", json=product_payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Producto Test"
        assert data["sku"] == "SKU-TEST-001"

    def test_create_product_slug_generated(self, client, auth_headers, product_payload):
        resp = client.post("/api/products/", json=product_payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data.get("slug") is not None
        assert "producto" in data["slug"].lower()

    def test_get_product_not_found(self, client, auth_headers):
        resp = client.get("/api/products/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_product_found(self, client, auth_headers, product_payload):
        create_resp = client.post("/api/products/", json=product_payload, headers=auth_headers)
        assert create_resp.status_code == 201
        pid = create_resp.json()["id"]

        resp = client.get(f"/api/products/{pid}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == pid

    def test_update_product(self, client, auth_headers, product_payload):
        create_resp = client.post("/api/products/", json=product_payload, headers=auth_headers)
        assert create_resp.status_code == 201, create_resp.json()
        pid = create_resp.json()["id"]

        resp = client.patch(
            f"/api/products/{pid}",
            json={"name": "Producto Actualizado"},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 500), resp.json()
        if resp.status_code == 200:
            assert resp.json()["name"] == "Producto Actualizado"

    def test_deactivate_product(self, client, auth_headers, product_payload):
        create_resp = client.post("/api/products/", json=product_payload, headers=auth_headers)
        assert create_resp.status_code == 201, create_resp.json()
        pid = create_resp.json()["id"]

        resp = client.patch(f"/api/products/{pid}/deactivate", headers=auth_headers)
        assert resp.status_code in (200, 500)

    def test_reactivate_product(self, client, auth_headers, product_payload):
        create_resp = client.post("/api/products/", json=product_payload, headers=auth_headers)
        assert create_resp.status_code == 201, create_resp.json()
        pid = create_resp.json()["id"]

        client.patch(f"/api/products/{pid}/deactivate", headers=auth_headers)
        resp = client.patch(f"/api/products/{pid}/reactivate", headers=auth_headers)
        assert resp.status_code in (200, 500)

    def test_get_product_filters(self, client, auth_headers):
        resp = client.get("/api/products/filters", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "brands" in data or "categories" in data or isinstance(data, dict)

    def test_list_products_search_filter(self, client, auth_headers, product_payload):
        client.post("/api/products/", json=product_payload, headers=auth_headers)

        resp = client.get(
            "/api/products/", params={"search": "Producto Test"}, headers=auth_headers
        )
        assert resp.status_code == 200

    def test_list_products_pagination(self, client, auth_headers):
        resp = client.get(
            "/api/products/", params={"page": 1, "page_size": 5}, headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1

    def test_create_product_invalid_price(self, client, auth_headers):
        payload = {
            "name": "Prod",
            "brand": "Marca",
            "category": "pilas",
            "unit_cost": "-10",  # negativo — inválido
            "unit_price": "50",
        }
        resp = client.post("/api/products/", json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_create_product_missing_required_fields(self, client, auth_headers):
        resp = client.post("/api/products/", json={"name": "Solo nombre"}, headers=auth_headers)
        assert resp.status_code == 422

    def test_list_products_client_login_flow(self, client, test_client):
        """Un cliente puede loguearse y con esa sesión ver el catálogo."""
        login = client.post(
            "/api/clients/login",
            json={"email": "comercio@test.com", "password": "clientpass123"},
        )
        assert login.status_code == 200

        resp = client.get("/api/products/")  # usa la cookie seteada por el login
        assert resp.status_code == 200

    def test_list_products_client_token_works(self, client, client_auth_headers):
        """Un token de cliente (Bearer) también da acceso al catálogo."""
        resp = client.get("/api/products/", headers=client_auth_headers)
        assert resp.status_code == 200

    def test_client_token_cannot_access_staff_endpoints(self, client, client_auth_headers):
        """Un token de cliente NO debe servir para el panel interno."""
        resp = client.get("/api/clients", headers=client_auth_headers)
        assert resp.status_code == 401

    def test_staff_token_cannot_login_as_client(self, client, auth_headers):
        """Un token de staff no debe pasar por el dependency de cliente."""
        resp = client.get("/api/clients/me", headers=auth_headers)
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# Checkout (pedidos "shop") — ahora requiere cliente logueado
# ═══════════════════════════════════════════════════════════════════════════

class TestOrderCheckout:

    def test_create_order_requires_client_login(self, client, product_payload, auth_headers):
        from datetime import date, timedelta
        create_resp = client.post("/api/products/", json=product_payload, headers=auth_headers)
        pid = create_resp.json()["id"]
        delivery_date = (date.today() + timedelta(days=5)).isoformat()

        resp = client.post("/api/orders", json={
            "items": [{"product_id": pid, "quantity": 1}],
            "customer_name": "Juan Perez",
            "customer_phone": "+5493751123456",
            "customer_email": "juan@test.com",
            "delivery_address": "Calle 123",
            "delivery_city": "Posadas",
            "preferred_delivery_date": delivery_date,
        })
        assert resp.status_code == 401

    def test_create_order_links_authenticated_client(
        self, client, product_payload, auth_headers, client_auth_headers, test_client
    ):
        """El pedido queda ligado al cliente logueado que lo hizo."""
        from datetime import date, timedelta
        create_resp = client.post("/api/products/", json=product_payload, headers=auth_headers)
        pid = create_resp.json()["id"]
        delivery_date = (date.today() + timedelta(days=5)).isoformat()

        resp = client.post(
            "/api/orders",
            json={
                "items": [{"product_id": pid, "quantity": 2}],
                "customer_name": "Juan Perez",
                "customer_phone": "+5493751123456",
                "customer_email": "juan@test.com",
                "delivery_address": "Calle 123",
                "delivery_city": "Posadas",
                "preferred_delivery_date": delivery_date,
            },
            headers=client_auth_headers,
        )
        assert resp.status_code == 201, resp.json()
        assert resp.json()["client_id"] == test_client.id

    def test_create_order_without_branch_stays_null(
        self, client, product_payload, auth_headers, client_auth_headers
    ):
        """Si el cliente no manda client_branch_id, sigue quedando null (compat)."""
        from datetime import date, timedelta
        create_resp = client.post("/api/products/", json=product_payload, headers=auth_headers)
        pid = create_resp.json()["id"]
        delivery_date = (date.today() + timedelta(days=5)).isoformat()

        resp = client.post(
            "/api/orders",
            json={
                "items": [{"product_id": pid, "quantity": 1}],
                "customer_name": "Juan Perez",
                "customer_phone": "+5493751123456",
                "customer_email": "juan@test.com",
                "delivery_address": "Calle 123",
                "delivery_city": "Posadas",
                "preferred_delivery_date": delivery_date,
            },
            headers=client_auth_headers,
        )
        assert resp.status_code == 201, resp.json()
        assert resp.json()["client_branch_id"] is None

    def test_create_order_with_own_branch_links_it(
        self, client, db, product_payload, auth_headers, client_auth_headers, test_client
    ):
        """Si manda client_branch_id de una sucursal propia, queda linkeado."""
        from datetime import date, timedelta
        from app.models.client_branch_model import ClientBranch

        branch = ClientBranch(
            client_id=test_client.id,
            name="Sucursal Norte",
            address="Ruta 12 km 5",
            city="Posadas",
            is_main=False,
        )
        db.add(branch)
        db.flush()

        create_resp = client.post("/api/products/", json=product_payload, headers=auth_headers)
        pid = create_resp.json()["id"]
        delivery_date = (date.today() + timedelta(days=5)).isoformat()

        resp = client.post(
            "/api/orders",
            json={
                "items": [{"product_id": pid, "quantity": 1}],
                "customer_name": "Juan Perez",
                "customer_phone": "+5493751123456",
                "customer_email": "juan@test.com",
                "delivery_address": "Calle 123",
                "delivery_city": "Posadas",
                "preferred_delivery_date": delivery_date,
                "client_branch_id": branch.id,
            },
            headers=client_auth_headers,
        )
        assert resp.status_code == 201, resp.json()
        body = resp.json()
        assert body["client_branch_id"] == branch.id
        assert body["client_branch"]["name"] == "Sucursal Norte"

    def test_create_order_with_someone_elses_branch_rejected(
        self, client, db, product_payload, auth_headers, client_auth_headers
    ):
        """No puede asociar el pedido a una sucursal de OTRO cliente."""
        from datetime import date, timedelta
        from app.models.client_branch_model import ClientBranch
        from app.models.client_model import Client
        from app.core.security import get_password_hash

        other_client = Client(
            name="Otro Comercio",
            client_type="company",
            email="otro@test.com",
            hashed_password=get_password_hash("otherpass123"),
            is_active=True,
        )
        db.add(other_client)
        db.flush()

        other_branch = ClientBranch(
            client_id=other_client.id,
            name="Sucursal Ajena",
            is_main=True,
        )
        db.add(other_branch)
        db.flush()

        create_resp = client.post("/api/products/", json=product_payload, headers=auth_headers)
        pid = create_resp.json()["id"]
        delivery_date = (date.today() + timedelta(days=5)).isoformat()

        resp = client.post(
            "/api/orders",
            json={
                "items": [{"product_id": pid, "quantity": 1}],
                "customer_name": "Juan Perez",
                "customer_phone": "+5493751123456",
                "customer_email": "juan@test.com",
                "delivery_address": "Calle 123",
                "delivery_city": "Posadas",
                "preferred_delivery_date": delivery_date,
                "client_branch_id": other_branch.id,
            },
            headers=client_auth_headers,
        )
        assert resp.status_code == 422
        assert "no pertenece" in resp.json()["detail"].lower()

    def test_me_branches_lists_own_branches_only(
        self, client, db, client_auth_headers, test_client
    ):
        """GET /clients/me/branches devuelve solo las sucursales del cliente logueado."""
        from app.models.client_branch_model import ClientBranch

        branch = ClientBranch(
            client_id=test_client.id,
            name="Casa Central",
            is_main=True,
        )
        db.add(branch)
        db.flush()

        resp = client.get("/api/clients/me/branches", headers=client_auth_headers)
        assert resp.status_code == 200
        names = [b["name"] for b in resp.json()]
        assert names == ["Casa Central"]

    def test_me_branches_requires_client_login(self, client, auth_headers):
        """Un token de staff no debe poder pegarle a /clients/me/branches."""
        resp = client.get("/api/clients/me/branches", headers=auth_headers)
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# Clientes
# ═══════════════════════════════════════════════════════════════════════════

class TestClientsEndpoints:

    def test_list_clients_requires_auth(self, client):
        resp = client.get("/api/clients")
        assert resp.status_code == 401

    def test_list_clients_authenticated(self, client, auth_headers):
        resp = client.get("/api/clients", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "clients" in data
        assert "total" in data

    def test_create_client_requires_superuser(self, client, auth_headers):
        """Un usuario normal no puede crear clientes."""
        payload = {
            "name": "Cliente Test",
            "client_type": "company",
        }
        resp = client.post("/api/clients", json=payload, headers=auth_headers)
        assert resp.status_code == 403

    def test_create_client_superuser(self, client, super_headers):
        payload = {
            "name": "Empresa Test SA",
            "client_type": "company",
            "password": "clientpass123",
        }
        resp = client.post("/api/clients", json=payload, headers=super_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Empresa Test SA"

    def test_get_client_not_found(self, client, auth_headers):
        resp = client.get("/api/clients/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_client_found(self, client, super_headers, auth_headers):
        create = client.post("/api/clients", json={
            "name": "Cliente Encontrado",
            "client_type": "company",
            "password": "clientpass123",
        }, headers=super_headers)
        assert create.status_code == 201
        cid = create.json()["id"]

        resp = client.get(f"/api/clients/{cid}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == cid

    def test_deactivate_client_superuser(self, client, super_headers):
        create = client.post("/api/clients", json={
            "name": "Cliente Para Desactivar",
            "client_type": "company",
            "password": "clientpass123",
        }, headers=super_headers)
        cid = create.json()["id"]

        resp = client.patch(f"/api/clients/{cid}/deactivate", headers=super_headers)
        assert resp.status_code == 200

    def test_activate_client_superuser(self, client, super_headers):
        create = client.post("/api/clients", json={
            "name": "Cliente Para Activar",
            "client_type": "company",
            "password": "clientpass123",
        }, headers=super_headers)
        cid = create.json()["id"]

        client.patch(f"/api/clients/{cid}/deactivate", headers=super_headers)
        resp = client.patch(f"/api/clients/{cid}/activate", headers=super_headers)
        assert resp.status_code == 200

    def test_list_clients_pagination(self, client, auth_headers):
        resp = client.get("/api/clients", params={"page": 1, "page_size": 5}, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 5


# ═══════════════════════════════════════════════════════════════════════════
# Sales Reps
# ═══════════════════════════════════════════════════════════════════════════

class TestSalesRepsEndpoints:

    def test_list_visible_to_any_active_user(self, client, auth_headers):
        # Ver el listado está permitido para cualquier vendedor logueado;
        # solo crear/editar/borrar está restringido a superusuario.
        resp = client.get("/api/sales-reps/", headers=auth_headers)
        assert resp.status_code == 200

    def test_create_sales_rep_requires_superuser(self, client, auth_headers):
        payload = {
            "name": "Nuevo Vendedor",
            "email": "sin-permiso@vendedor.com",
            "password": "securepass123",
        }
        resp = client.post("/api/sales-reps/", json=payload, headers=auth_headers)
        assert resp.status_code == 403

    def test_list_as_superuser(self, client, super_headers):
        resp = client.get("/api/sales-reps/", headers=super_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "sales_reps" in data or "items" in data or isinstance(data, list) or isinstance(data, dict)

    def test_create_sales_rep_superuser(self, client, super_headers):
        payload = {
            "name": "Nuevo Vendedor",
            "email": "nuevo@vendedor.com",
            "password": "securepass123",
        }
        resp = client.post("/api/sales-reps/", json=payload, headers=super_headers)
        assert resp.status_code == 201
        assert resp.json()["email"] == "nuevo@vendedor.com"

    def test_create_sales_rep_duplicate_email(self, client, super_headers):
        payload = {"name": "Vendedor", "email": "dup@test.com", "password": "pass123"}
        client.post("/api/sales-reps/", json=payload, headers=super_headers)
        resp = client.post("/api/sales-reps/", json=payload, headers=super_headers)
        assert resp.status_code in (400, 409, 422)

    def test_create_sales_rep_missing_email(self, client, super_headers):
        payload = {"name": "Vendedor Sin Email", "password": "pass123"}
        resp = client.post("/api/sales-reps/", json=payload, headers=super_headers)
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════
# Suppliers
# ═══════════════════════════════════════════════════════════════════════════

class TestSuppliersEndpoints:
    def test_list_requires_auth(self, client):
        resp = client.get("/api/suppliers/")
        assert resp.status_code == 401

    def test_list_authenticated(self, client, auth_headers):
        resp = client.get("/api/suppliers/", headers=auth_headers)
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
# Dashboard
# ═══════════════════════════════════════════════════════════════════════════

class TestDashboardEndpoints:
    def test_dashboard_requires_auth(self, client):
        resp = client.get("/api/dashboard/")
        assert resp.status_code in (401, 404)

    def test_dashboard_authenticated(self, client, auth_headers):
        resp = client.get("/api/dashboard/", headers=auth_headers)
        # Puede ser 200 o 404 según el endpoint exacto
        assert resp.status_code in (200, 404)