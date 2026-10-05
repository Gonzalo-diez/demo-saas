"""
test_tenant_isolation.py — Garantías multi-tenant (SaaS de distribuidoras).

Cada distribuidora es un tenant. Estos tests verifican de punta a punta que:
- el login es por tenant (el mismo email puede existir en dos distribuidoras),
- el tenant de un request sale del JWT firmado y NO de un header,
- ningún endpoint devuelve ni modifica datos de otro tenant,
- las rutas de administración de tenants exigen la clave de plataforma.
"""
import pytest
from jose import jwt as jose_jwt
from sqlalchemy import select

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.db.tenant_context import (
    TenantContextError,
    set_tenant,
    tenant_scope,
    unscoped,
)
from app.models.admin_model import Admin
from app.models.client_model import Client
from app.models.product_model import Product
from app.models.sales_rep_model import SalesRep
from app.models.tenant_model import Tenant


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _make_tenant(db, *, name, slug, is_active=True) -> Tenant:
    with unscoped(db):
        tenant = Tenant(name=name, slug=slug, domain=f"{slug}.localhost", is_active=is_active)
        db.add(tenant)
        db.flush()
    return tenant


def _make_rep(db, tenant, *, email, password="testpass123", superuser=True) -> SalesRep:
    with tenant_scope(db, tenant.id):
        rep = SalesRep(
            name=f"Rep {email}",
            email=email,
            hashed_password=get_password_hash(password),
            is_active=True,
            is_superuser=superuser,
        )
        db.add(rep)
        db.flush()
    return rep


def _make_client(db, tenant, *, email) -> Client:
    with tenant_scope(db, tenant.id):
        c = Client(
            name=f"Comercio {email}",
            client_type="company",
            email=email,
            hashed_password=get_password_hash("clientpass123"),
            is_active=True,
        )
        db.add(c)
        db.flush()
    return c


def _bearer(rep: SalesRep) -> dict:
    token = create_access_token(str(rep.id), tenant_id=rep.tenant_id)
    return {"Authorization": f"Bearer {token}"}


def _admin_bearer(admin: Admin) -> dict:
    token = create_access_token(str(admin.id), token_type="platform_admin")
    return {"Authorization": f"Bearer {token}"}


def _product_payload(sku="SKU-001", name="Producto"):
    return {
        "name": name,
        "brand": "Marca",
        "category": "pilas",
        "unit_cost": "100.00",
        "unit_price": "150.00",
        "sku": sku,
        "stock_current": 10,
        "stock_min": 2,
        "image_url": "https://example.com/image.jpg",
    }


@pytest.fixture()
def tenant_b(db):
    return _make_tenant(db, name="Distribuidora B", slug="dist-b")


@pytest.fixture()
def rep_a(db, tenant):
    return _make_rep(db, tenant, email="admin@a.com")


@pytest.fixture()
def rep_b(db, tenant_b):
    return _make_rep(db, tenant_b, email="admin@b.com")


# ═══════════════════════════════════════════════════════════════════════════
# Login por tenant
# ═══════════════════════════════════════════════════════════════════════════

class TestLoginPerTenant:
    def test_same_email_in_two_tenants_each_gets_own_user(self, client, db, tenant, tenant_b):
        rep_a = _make_rep(db, tenant, email="shared@x.com", password="passwordA")
        rep_b = _make_rep(db, tenant_b, email="shared@x.com", password="passwordB")

        resp_a = client.post(
            "/api/sales-reps/login",
            json={"email": "shared@x.com", "password": "passwordA"},
            headers={"X-Tenant-Slug": "test"},
        )
        assert resp_a.status_code == 200
        assert resp_a.json()["id"] == rep_a.id

        resp_b = client.post(
            "/api/sales-reps/login",
            json={"email": "shared@x.com", "password": "passwordB"},
            headers={"X-Tenant-Slug": "dist-b"},
        )
        assert resp_b.status_code == 200
        assert resp_b.json()["id"] == rep_b.id

    def test_token_carries_the_tenant(self, client, db, tenant_b, rep_b):
        resp = client.post(
            "/api/sales-reps/login",
            json={"email": "admin@b.com", "password": "testpass123"},
            headers={"X-Tenant-Slug": "dist-b"},
        )
        assert resp.status_code == 200
        token = resp.cookies.get(settings.AUTH_COOKIE_NAME)
        payload = jose_jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        assert payload["tenant_id"] == tenant_b.id

    def test_credentials_of_other_tenant_rejected(self, client, db, rep_b):
        """admin@b.com existe solo en la distribuidora B: en A no entra."""
        resp = client.post(
            "/api/sales-reps/login",
            json={"email": "admin@b.com", "password": "testpass123"},
            headers={"X-Tenant-Slug": "test"},
        )
        assert resp.status_code == 401

    def test_login_without_tenant_is_400(self, client, db, rep_a):
        resp = client.post(
            "/api/sales-reps/login",
            json={"email": "admin@a.com", "password": "testpass123"},
            headers={"X-Tenant-Slug": ""},
        )
        assert resp.status_code == 400

    def test_login_unknown_tenant_is_400(self, client, db, rep_a):
        resp = client.post(
            "/api/sales-reps/login",
            json={"email": "admin@a.com", "password": "testpass123"},
            headers={"X-Tenant-Slug": "no-existe"},
        )
        assert resp.status_code == 400

    def test_tenant_slug_in_body_has_priority_over_header(self, client, db, rep_b):
        resp = client.post(
            "/api/sales-reps/login",
            json={"email": "admin@b.com", "password": "testpass123", "tenant_slug": "dist-b"},
            headers={"X-Tenant-Slug": "test"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == rep_b.id

    def test_inactive_tenant_cannot_login(self, client, db):
        inactive = _make_tenant(db, name="Cerrada", slug="cerrada", is_active=False)
        _make_rep(db, inactive, email="admin@cerrada.com")
        resp = client.post(
            "/api/sales-reps/login",
            json={"email": "admin@cerrada.com", "password": "testpass123"},
            headers={"X-Tenant-Slug": "cerrada"},
        )
        assert resp.status_code == 403

    def test_client_login_is_per_tenant(self, client, db, tenant, tenant_b):
        cb = _make_client(db, tenant_b, email="comercio@b.com")

        wrong = client.post(
            "/api/clients/login",
            json={"email": "comercio@b.com", "password": "clientpass123"},
            headers={"X-Tenant-Slug": "test"},
        )
        assert wrong.status_code == 401

        ok = client.post(
            "/api/clients/login",
            json={"email": "comercio@b.com", "password": "clientpass123"},
            headers={"X-Tenant-Slug": "dist-b"},
        )
        assert ok.status_code == 200
        assert ok.json()["id"] == cb.id


# ═══════════════════════════════════════════════════════════════════════════
# El tenant sale del token, no del header
# ═══════════════════════════════════════════════════════════════════════════

class TestTenantComesFromToken:
    def test_header_cannot_override_token_tenant(self, client, db, rep_a, rep_b):
        client.post("/api/products/", json=_product_payload("A-1", "Prod A"), headers=_bearer(rep_a))
        client.post("/api/products/", json=_product_payload("B-1", "Prod B"), headers=_bearer(rep_b))

        # Token de A pero pidiendo "ser" B por header: igual ve solo lo de A.
        headers = {**_bearer(rep_a), "X-Tenant-Slug": "dist-b", "X-Tenant-ID": "999"}
        resp = client.get("/api/products/", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

        with tenant_scope(db, rep_a.tenant_id):
            names = [p.name for p in db.scalars(select(Product))]
        assert names == ["Prod A"]

    def test_token_without_tenant_claim_rejected(self, client, db, rep_a):
        legacy = jose_jwt.encode(
            {"sub": str(rep_a.id), "type": "staff"},
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALG,
        )
        resp = client.get("/api/sales-reps/me", headers={"Authorization": f"Bearer {legacy}"})
        assert resp.status_code == 401

    def test_forged_tenant_claim_cannot_reach_other_users(self, client, db, rep_a, tenant_b):
        """Un user id de A con claim de tenant B no existe en B → 401."""
        forged = create_access_token(str(rep_a.id), tenant_id=tenant_b.id)
        resp = client.get("/api/sales-reps/me", headers={"Authorization": f"Bearer {forged}"})
        assert resp.status_code == 401

    def test_token_of_inactive_tenant_rejected(self, client, db, tenant_b, rep_b):
        with unscoped(db):
            tenant_b.is_active = False
            db.flush()
        resp = client.get("/api/sales-reps/me", headers=_bearer(rep_b))
        assert resp.status_code == 403

    def test_my_tenant_endpoint(self, client, db, tenant, rep_a):
        resp = client.get("/api/tenants/me", headers=_bearer(rep_a))
        assert resp.status_code == 200
        assert resp.json()["id"] == tenant.id


# ═══════════════════════════════════════════════════════════════════════════
# Aislamiento de datos
# ═══════════════════════════════════════════════════════════════════════════

class TestDataIsolation:
    def test_products_are_isolated_and_sku_is_unique_per_tenant(self, client, db, rep_a, rep_b):
        # El MISMO sku en dos distribuidoras es válido (unique por tenant).
        ra = client.post("/api/products/", json=_product_payload("SKU-X", "Alfajor A"), headers=_bearer(rep_a))
        rb = client.post("/api/products/", json=_product_payload("SKU-X", "Alfajor B"), headers=_bearer(rep_b))
        assert ra.status_code == 201
        assert rb.status_code == 201
        assert ra.json()["id"] != rb.json()["id"]

        list_a = client.get("/api/products/", headers=_bearer(rep_a)).json()
        list_b = client.get("/api/products/", headers=_bearer(rep_b)).json()
        assert list_a["total"] == 1
        assert list_b["total"] == 1

    def test_created_rows_are_stamped_with_callers_tenant(self, client, db, tenant, tenant_b, rep_a, rep_b):
        client.post("/api/products/", json=_product_payload("SKU-A"), headers=_bearer(rep_a))
        client.post("/api/products/", json=_product_payload("SKU-B"), headers=_bearer(rep_b))
        with unscoped(db):
            rows = {p.sku: p.tenant_id for p in db.scalars(select(Product))}
        assert rows == {"SKU-A": tenant.id, "SKU-B": tenant_b.id}

    def test_cannot_read_other_tenants_product_by_id(self, client, db, rep_a, rep_b):
        pid_b = client.post(
            "/api/products/", json=_product_payload("B-ONLY"), headers=_bearer(rep_b)
        ).json()["id"]

        assert client.get(f"/api/products/{pid_b}", headers=_bearer(rep_b)).status_code == 200
        assert client.get(f"/api/products/{pid_b}", headers=_bearer(rep_a)).status_code == 404

    def test_cannot_modify_other_tenants_product(self, client, db, rep_a, rep_b):
        pid_b = client.post(
            "/api/products/", json=_product_payload("B-ONLY"), headers=_bearer(rep_b)
        ).json()["id"]

        patch = client.patch(f"/api/products/{pid_b}", json={"name": "Hackeado"}, headers=_bearer(rep_a))
        assert patch.status_code == 404
        deact = client.patch(f"/api/products/{pid_b}/deactivate", headers=_bearer(rep_a))
        assert deact.status_code == 404

        still = client.get(f"/api/products/{pid_b}", headers=_bearer(rep_b)).json()
        assert still["name"] == "Producto"
        assert still["is_active"] is True

    def test_clients_are_isolated(self, client, db, rep_a, rep_b, tenant_b):
        cb = _make_client(db, tenant_b, email="comercio@b.com")

        assert client.get(f"/api/clients/{cb.id}", headers=_bearer(rep_a)).status_code == 404
        listing = client.get("/api/clients", headers=_bearer(rep_a)).json()
        assert listing["total"] == 0
        assert client.get("/api/clients", headers=_bearer(rep_b)).json()["total"] == 1

    def test_sales_reps_list_only_own_tenant(self, client, db, rep_a, rep_b):
        listing = client.get("/api/sales-reps/", headers=_bearer(rep_a)).json()
        emails = [r["email"] for r in listing["sales_reps"]]
        assert emails == ["admin@a.com"]

    def test_cannot_create_user_in_another_tenant(self, client, db, tenant, tenant_b, rep_a):
        """Aunque el body traiga tenant_id de otra distribuidora, se ignora."""
        resp = client.post(
            "/api/sales-reps/",
            json={
                "name": "Intruso",
                "email": "intruso@x.com",
                "password": "secret123",
                "tenant_id": tenant_b.id,
            },
            headers=_bearer(rep_a),
        )
        assert resp.status_code == 201
        with unscoped(db):
            created = db.scalar(select(SalesRep).where(SalesRep.email == "intruso@x.com"))
        assert created.tenant_id == tenant.id

    def test_same_email_can_be_created_in_two_tenants(self, client, db, rep_a, rep_b):
        body = {"name": "Vendedor", "email": "vendedor@x.com", "password": "secret123"}
        assert client.post("/api/sales-reps/", json=body, headers=_bearer(rep_a)).status_code == 201
        assert client.post("/api/sales-reps/", json=body, headers=_bearer(rep_b)).status_code == 201
        # ...pero no dos veces en el mismo tenant
        assert client.post("/api/sales-reps/", json=body, headers=_bearer(rep_a)).status_code == 400

    def test_client_token_is_scoped_too(self, client, db, tenant, tenant_b, rep_b):
        cb = _make_client(db, tenant_b, email="comercio@b.com")
        cat = client.post("/api/categories/", json={"name": "Pilas", "image_url": "https://example.com/p.jpg"}, headers=_bearer(rep_b)).json()
        client.post(
            "/api/products/",
            json={**_product_payload("B-1"), "category": None, "category_id": cat["id"]},
            headers=_bearer(rep_b),
        )
        token = create_access_token(str(cb.id), token_type="client", tenant_id=tenant_b.id)
        headers = {"Authorization": f"Bearer {token}"}

        assert client.get("/api/clients/me", headers=headers).json()["id"] == cb.id
        assert client.get("/api/products/", headers=headers).json()["total"] == 1

    def test_analytics_reads_require_auth(self, client):
        # Estos endpoints estaban abiertos: ahora exigen login.
        for url in (
            "/api/analytics/sales-reps/daily?target_date=2026-01-01",
            "/api/analytics/sales-reps/daily/1?target_date=2026-01-01",
            "/api/analytics/products/daily/1?target_date=2026-01-01",
            "/api/analytics/zones/products/daily?target_date=2026-01-01",
            "/api/analytics/zones/products/daily/abc?target_date=2026-01-01",
        ):
            assert client.get(url).status_code == 401, url

    def test_public_event_tracking_needs_a_tenant(self, client, db, tenant, tenant_b):
        event = {"visitor_id": "v1", "session_id": "s1", "event_type": "catalog_open"}

        ok = client.post("/api/analytics/events", json=event, headers={"X-Tenant-Slug": "dist-b"})
        assert ok.status_code == 201

        missing = client.post("/api/analytics/events", json=event, headers={"X-Tenant-Slug": ""})
        assert missing.status_code == 400

        from app.analytics.models.analytics_catalog_event_model import AnalyticsCatalogEvent
        with unscoped(db):
            tenants = [e.tenant_id for e in db.scalars(select(AnalyticsCatalogEvent))]
        assert tenants == [tenant_b.id]


# ═══════════════════════════════════════════════════════════════════════════
# Administración de la plataforma (alta de distribuidoras)
# ═══════════════════════════════════════════════════════════════════════════

class TestPlatformAdmin:
    """Las distribuidoras las gestiona un admin de plataforma (tabla admins)."""

    @pytest.fixture
    def admin(self, db):
        a = Admin(name="Plataforma", email="root@platform.com",
                  hashed_password=get_password_hash("rootpass123"), is_active=True)
        db.add(a)
        db.flush()
        return a

    @pytest.fixture
    def headers(self, admin):
        return _admin_bearer(admin)

    def test_tenant_management_requires_platform_admin(self, client, db, rep_a, admin):
        assert client.get("/api/tenants/").status_code == 401
        # Un superusuario de una distribuidora NO es admin de la plataforma.
        assert client.get("/api/tenants/", headers=_bearer(rep_a)).status_code == 401
        assert client.post(
            "/api/tenants/", json={"name": "X", "slug": "x"}, headers=_bearer(rep_a)
        ).status_code == 401
        assert client.patch("/api/tenants/1/deactivate").status_code == 401

    def test_platform_admin_token_is_useless_in_tenant_routes(self, client, db, rep_a, admin):
        h = _admin_bearer(admin)
        assert client.get("/api/sales-reps/me", headers=h).status_code == 401
        assert client.get("/api/tenants/me", headers=h).status_code == 401
        # El catálogo es público: con un token que no es de la tienda se lo trata como visitante
        # anónimo (solo lo publicado), nunca como personal.
        assert client.get("/api/products/", headers=h).status_code == 200

    def test_inactive_platform_admin_is_rejected(self, client, db, admin):
        admin.is_active = False
        db.flush()
        assert client.get("/api/tenants/", headers=_admin_bearer(admin)).status_code == 403

    def test_platform_admin_login_and_me(self, client, db, admin):
        bad = client.post("/api/admin/login", json={"email": "root@platform.com", "password": "mala"})
        assert bad.status_code == 401
        ok = client.post("/api/admin/login", json={"email": "root@platform.com", "password": "rootpass123"})
        assert ok.status_code == 200
        token = ok.cookies.get(settings.PLATFORM_AUTH_COOKIE_NAME)
        claims = jose_jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        assert claims["type"] == "platform_admin" and "tenant_id" not in claims
        # La cookie de plataforma es distinta de la de distribuidora
        assert settings.AUTH_COOKIE_NAME not in ok.cookies
        assert client.get("/api/admin/me").json()["email"] == "root@platform.com"

    def test_platform_admin_cannot_remove_self(self, client, db, admin, headers):
        assert client.patch(f"/api/admin/users/{admin.id}", json={"is_active": False}, headers=headers).status_code == 400
        assert client.delete(f"/api/admin/users/{admin.id}", headers=headers).status_code == 400

    def test_create_second_platform_admin(self, client, db, admin, headers):
        resp = client.post(
            "/api/admin/users",
            json={"name": "Otro", "email": "otro@platform.com", "password": "otro12345"},
            headers=headers,
        )
        assert resp.status_code == 201
        assert client.post(
            "/api/admin/users",
            json={"name": "Dup", "email": "otro@platform.com", "password": "otro12345"},
            headers=headers,
        ).status_code == 409

    def test_tenant_creates_its_own_sales_reps_and_they_stay_inside(self, client, db, headers):
        client.post(
            "/api/tenants/",
            json={"name": "Nueva A", "slug": "nueva-a", "domain": "nueva-a.localhost", "admin_email": "o@a.com", "admin_password": "secret123"},
            headers=headers,
        )
        client.post(
            "/api/tenants/",
            json={"name": "Nueva B", "slug": "nueva-b", "domain": "nueva-b.localhost", "admin_email": "o@b.com", "admin_password": "secret123"},
            headers=headers,
        )
        login = client.post("/api/sales-reps/login", json={"email": "o@a.com", "password": "secret123"},
                            headers={"X-Tenant-Slug": "nueva-a"})
        assert login.status_code == 200
        owner_a = {"Authorization": f"Bearer {login.cookies.get(settings.AUTH_COOKIE_NAME)}"}

        created = client.post(
            "/api/sales-reps/",
            json={"name": "Vendedor", "email": "v@a.com", "password": "vend12345"},
            headers=owner_a,
        )
        assert created.status_code == 201
        assert created.json()["is_superuser"] is False

        # El vendedor entra solo a su distribuidora y no puede crear más vendedores
        assert client.post("/api/sales-reps/login", json={"email": "v@a.com", "password": "vend12345"},
                           headers={"X-Tenant-Slug": "nueva-b"}).status_code == 401
        v = client.post("/api/sales-reps/login", json={"email": "v@a.com", "password": "vend12345"},
                        headers={"X-Tenant-Slug": "nueva-a"})
        assert v.status_code == 200
        v_headers = {"Authorization": f"Bearer {v.cookies.get(settings.AUTH_COOKIE_NAME)}"}
        assert client.post(
            "/api/sales-reps/",
            json={"name": "X", "email": "x@a.com", "password": "vend12345"},
            headers=v_headers,
        ).status_code == 403

    def test_provision_new_distributor_with_admin_and_login(self, client, db, headers):
        resp = client.post(
            "/api/tenants/",
            json={
                "name": "Distribuidora Nueva",
                "slug": "nueva",
                "domain": "https://Tienda.Nueva.com/catalogo",
                "admin_email": "dueño@nueva.com",
                "admin_password": "secret123",
                "admin_name": "Dueño",
            },
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        new_id = resp.json()["id"]
        assert resp.json()["domain"] == "tienda.nueva.com"  # se guarda solo el host

        login = client.post(
            "/api/sales-reps/login",
            json={"email": "dueño@nueva.com", "password": "secret123"},
            headers={"X-Tenant-Slug": "nueva"},
        )
        assert login.status_code == 200
        assert login.json()["is_superuser"] is True

        token = login.cookies.get(settings.AUTH_COOKIE_NAME)
        assert jose_jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])["tenant_id"] == new_id

        listing = client.get("/api/tenants/", headers=headers).json()
        assert {t["slug"] for t in listing["items"]} >= {"test", "nueva"}

    def test_provision_rejects_duplicates_and_bad_slugs(self, client, db, headers):
        assert client.post("/api/tenants/", json={"name": "Otra", "slug": "test", "domain": "otra.localhost"}, headers=headers).status_code == 409
        assert client.post("/api/tenants/", json={"name": "Otra", "slug": "Mi Slug!", "domain": "otra.localhost"}, headers=headers).status_code == 422
        # admin_email sin password
        assert client.post(
            "/api/tenants/",
            json={"name": "Otra", "slug": "otra", "domain": "otra.localhost", "admin_email": "a@b.com"},
            headers=headers,
        ).status_code == 422

    def test_public_slug_lookup_hides_sensitive_data(self, client, db, tenant_b):
        resp = client.get("/api/tenants/slug/dist-b")
        assert resp.status_code == 200
        assert set(resp.json()) == {"id", "name", "slug", "domain", "logo_url"}

    def test_deactivate_blocks_everything(self, client, db, tenant_b, rep_b, headers):
        assert client.patch(f"/api/tenants/{tenant_b.id}/deactivate", headers=headers).status_code == 200

        assert client.get("/api/sales-reps/me", headers=_bearer(rep_b)).status_code == 403
        assert client.get("/api/tenants/slug/dist-b").status_code == 404
        login = client.post(
            "/api/sales-reps/login",
            json={"email": "admin@b.com", "password": "testpass123"},
            headers={"X-Tenant-Slug": "dist-b"},
        )
        assert login.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════
# Capa de sesión (sin HTTP)
# ═══════════════════════════════════════════════════════════════════════════

class TestSessionLevelIsolation:
    def test_queries_are_filtered_by_session_tenant(self, db, tenant, tenant_b):
        for t, name in ((tenant, "a"), (tenant_b, "b")):
            with tenant_scope(db, t.id):
                db.add(Product(name=name, name_normalized=name, brand="m", brand_normalized="m",
                               category="c", category_normalized="c", slug=name, sku=name,
                               unit_price=1, unit_cost=1, stock_current=1))
                db.flush()

        with tenant_scope(db, tenant.id):
            assert [p.name for p in db.scalars(select(Product))] == ["a"]
        with tenant_scope(db, tenant_b.id):
            assert [p.name for p in db.scalars(select(Product))] == ["b"]

    def test_session_without_tenant_sees_nothing(self, db, tenant):
        with tenant_scope(db, tenant.id):
            db.add(Product(name="a", name_normalized="a", brand="m", brand_normalized="m",
                           category="c", category_normalized="c", slug="a", sku="a",
                           unit_price=1, unit_cost=1, stock_current=1))
            db.flush()
        db.info.pop("tenant_id")
        assert db.scalars(select(Product)).all() == []

    def test_insert_without_tenant_fails(self, db):
        db.info.pop("tenant_id")
        db.add(SalesRep(name="x", email="x@x.com", hashed_password="h"))
        with pytest.raises(TenantContextError):
            db.flush()
        db.rollback()

    def test_insert_into_other_tenant_fails(self, db, tenant, tenant_b):
        set_tenant(db, tenant.id)
        db.add(SalesRep(name="x", email="x@x.com", hashed_password="h", tenant_id=tenant_b.id))
        with pytest.raises(TenantContextError):
            db.flush()
        db.rollback()

    def test_cannot_move_row_to_other_tenant(self, db, tenant, tenant_b, rep_a):
        set_tenant(db, tenant.id)
        rep = db.get(SalesRep, rep_a.id)
        rep.tenant_id = tenant_b.id
        with pytest.raises(TenantContextError):
            db.flush()
        db.rollback()


class TestJobsRunPerTenant:
    def test_job_runs_once_per_active_tenant_with_its_own_session(self, db, tenant, tenant_b, monkeypatch):
        from app.analytics.jobs import base_job
        from app.analytics.jobs.base_job import BaseAnalyticsJob
        from tests.conftest import TestingSessionLocal

        _make_tenant(db, name="Cerrada", slug="cerrada", is_active=False)
        connection = db.get_bind()
        monkeypatch.setattr(
            base_job,
            "SessionLocal",
            lambda: TestingSessionLocal(bind=connection, join_transaction_mode="create_savepoint"),
        )

        seen = []

        class Probe(BaseAnalyticsJob):
            job_name = "probe"

            def _run(self, db, target_date):
                seen.append(db.info["tenant_id"])

        Probe().run()
        assert sorted(seen) == sorted([tenant.id, tenant_b.id])  # la inactiva no corre

        seen.clear()
        Probe().run(tenant_id=tenant_b.id)
        assert seen == [tenant_b.id]

    def test_one_failing_tenant_does_not_stop_the_others(self, db, tenant, tenant_b, monkeypatch):
        from app.analytics.jobs import base_job
        from app.analytics.jobs.base_job import BaseAnalyticsJob
        from tests.conftest import TestingSessionLocal

        connection = db.get_bind()
        monkeypatch.setattr(
            base_job,
            "SessionLocal",
            lambda: TestingSessionLocal(bind=connection, join_transaction_mode="create_savepoint"),
        )
        seen = []

        class Flaky(BaseAnalyticsJob):
            job_name = "flaky"

            def _run(self, db, target_date):
                tid = db.info["tenant_id"]
                seen.append(tid)
                if tid == tenant.id:
                    raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            Flaky().run()
        assert sorted(seen) == sorted([tenant.id, tenant_b.id])
