"""
conftest.py — Fixtures compartidas para toda la suite de tests.

Usa SQLite en memoria para no depender de PostgreSQL.
"""
import os
import sqlite3
from decimal import Decimal
import pytest

# ── Adapter de Decimal para sqlite3 ─────────────────────────────────────────
# El driver sqlite3 no sabe bindear decimal.Decimal directamente (Postgres,
# el motor real en producción, sí). Sin esto, cualquier UPDATE/INSERT con un
# valor Decimal (ej. descontar stock) rompe únicamente contra la BD de test.
sqlite3.register_adapter(Decimal, str)

# ── Variables de entorno antes de importar la app ──────────────────────────
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("JWT_ALG", "HS256")
os.environ.setdefault("JWT_EXPIRES_MIN", "60")

from sqlalchemy import create_engine, event, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db.base import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.db.tenant_context import set_tenant, unscoped
from app.models.sales_rep_model import SalesRep
from app.models.client_model import Client
from app.models.tenant_model import Tenant

# ── Patch JSONB → JSON para SQLite ─────────────────────────────────────────
# Los modelos usan JSONB (solo disponible en PostgreSQL). Para el motor de
# tests (SQLite en memoria) mapeamos JSONB a JSON nativo.
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler

def _visit_JSONB(self, type_, **kw):
    return self.visit_JSON(type_, **kw)

SQLiteTypeCompiler.visit_JSONB = _visit_JSONB

# ── Engine SQLite en memoria ────────────────────────────────────────────────
SQLALCHEMY_TEST_URL = "sqlite://"  # pura memoria

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
)

# SQLite necesita PRAGMA foreign_keys para que las FK funcionen
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
    # pysqlite maneja el BEGIN/COMMIT por su cuenta (por detrás de
    # SQLAlchemy), lo cual rompe el aislamiento por SAVEPOINT en cuanto
    # un test hace más de un commit (ej. crear un producto y después
    # hacer un pedido: dos requests, dos commits). Recomendación oficial
    # de SQLAlchemy para pysqlite: desactivar su manejo propio de
    # transacciones y emitir el BEGIN nosotros mismos (ver evento
    # "begin" más abajo).
    # https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#serializable-isolation-savepoints-transactional-ddl
    dbapi_conn.isolation_level = None

@event.listens_for(engine, "begin")
def _do_begin(conn):
    conn.exec_driver_sql("BEGIN")

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Crea todas las tablas una sola vez por sesión de tests."""
    # Importar todos los modelos para que Base los conozca
    import app.models.sales_rep_model  # noqa
    import app.models.category_model  # noqa
    import app.models.product_model  # noqa
    import app.models.client_model  # noqa
    import app.models.client_branch_model  # noqa
    import app.models.supplier_model  # noqa
    import app.models.order_model  # noqa
    import app.models.order_item_model  # noqa
    import app.models.inventory_movement_model  # noqa
    import app.models.purchase_invoice_model  # noqa
    import app.models.sales_invoice_model  # noqa
    import app.models.sales_invoice_item_model  # noqa
    import app.models.purchase_invoice_item_model  # noqa
    import app.models.check_model  # noqa
    import app.models.tenant_model  # noqa
    import app.models.notification_model  # noqa
    # Analytics models (también necesarios para las relaciones)
    import app.analytics.models.analytics_catalog_event_model  # noqa
    import app.analytics.models.analytics_sales_rep_daily_model  # noqa
    import app.analytics.models.analytics_client_daily_model  # noqa
    import app.analytics.models.analytics_daily_model  # noqa
    import app.analytics.models.analytics_product_daily_model  # noqa
    import app.analytics.models.analytics_zone_product_daily_model  # noqa

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def db():
    """
    Sesión de BD aislada por test.
    Usa join_transaction_mode="create_savepoint" (soporte nativo de
    SQLAlchemy 2.0) para que cada db.commit() dentro de un endpoint/servicio
    libere y reabra un SAVEPOINT en vez de tocar la transacción externa.
    Es el reemplazo oficial del viejo hack manual con begin_nested() +
    evento "after_transaction_end", que se rompía si un servicio llamaba
    a db.commit() más de una vez dentro del mismo test (ej. un test que
    hace dos requests que commitean, como crear un producto y después
    hacer un pedido) — en ese caso, la segunda vuelta de commit terminaba
    commiteando la transacción externa de verdad, y los datos del test
    quedaban pegados para los tests siguientes.
    """
    connection = engine.connect()
    connection.begin()  # transacción externa — nunca se commitea
    session = TestingSessionLocal(bind=connection, join_transaction_mode="create_savepoint")

    # Multi-tenant: cada test arranca con un tenant "test" y la sesión atada a él,
    # igual que lo hace un request autenticado. Todo lo que el test cree queda
    # estampado con ese tenant.
    with unscoped(session):
        default_tenant = Tenant(name="Distribuidora Test", slug="test", domain="test.localhost", is_active=True)
        session.add(default_tenant)
        session.flush()
    set_tenant(session, default_tenant.id)
    session.info["default_tenant"] = default_tenant

    yield session

    session.close()
    connection.rollback()
    connection.close()

@pytest.fixture()
def client(db):
    """TestClient de FastAPI con la BD de test inyectada."""
    from app.main import app
    from app.db.base import get_db_with_commit
    from app.core.rate_limit import limiter

    # El rate limit vive en memoria y se acumularía entre tests (ej. 5 logins/min).
    limiter_was_enabled = limiter.enabled
    limiter.enabled = False

    def override_get_db():
        try:
            yield db
        finally:
            pass

    # Algunos endpoints usan get_db_with_commit (ej. login), otros get_db
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_db_with_commit] = override_get_db
    # Header de tenant por defecto: lo usan los endpoints de login (los
    # autenticados toman el tenant del token e ignoran este header).
    with TestClient(
        app,
        # TEST_RAISE=1 muestra el traceback real de un 500 al depurar.
        raise_server_exceptions=os.environ.get("TEST_RAISE") == "1",
        headers={"X-Tenant-Slug": "test"},
    ) as c:
        yield c
    app.dependency_overrides.clear()
    limiter.enabled = limiter_was_enabled

# ── Helpers para usuarios ───────────────────────────────────────────────────

def _make_sales_rep(db, *, email="test@test.com", is_superuser=False, is_active=True):
    rep = SalesRep(
        name="Test User",
        email=email,
        hashed_password=get_password_hash("testpass123"),
        is_active=is_active,
        is_superuser=is_superuser,
    )
    db.add(rep)
    db.flush()
    return rep

@pytest.fixture()
def tenant(db):
    """El tenant por defecto de los tests (la sesión ya está atada a él)."""
    return db.info["default_tenant"]


@pytest.fixture()
def sales_rep(db):
    return _make_sales_rep(db, email="rep@test.com")

@pytest.fixture()
def superuser(db):
    return _make_sales_rep(db, email="super@test.com", is_superuser=True)

@pytest.fixture()
def auth_headers(sales_rep):
    token = create_access_token(str(sales_rep.id), tenant_id=sales_rep.tenant_id)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture()
def super_headers(superuser):
    token = create_access_token(str(superuser.id), tenant_id=superuser.tenant_id)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture()
def test_client(db):
    """Un Client (comercio B2B) con password, para probar login/checkout."""
    c = Client(
        name="Comercio Test",
        client_type="company",
        email="comercio@test.com",
        hashed_password=get_password_hash("clientpass123"),
        is_active=True,
    )
    db.add(c)
    db.flush()
    return c

@pytest.fixture()
def client_auth_headers(test_client):
    token = create_access_token(
        str(test_client.id), token_type="client", tenant_id=test_client.tenant_id
    )
    return {"Authorization": f"Bearer {token}"}