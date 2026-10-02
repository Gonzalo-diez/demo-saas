"""
Seed de la demo SaaS: crea dos distribuidoras (tenants) con su administrador,
unos productos y un cliente B2B cada una. Es idempotente: se puede correr
varias veces.

Uso (con las migraciones ya aplicadas):

    python -m app.scripts.seed_demo

Credenciales que deja (contraseña de todos: demo1234):

    distribuidora  slug         admin                    cliente B2B
    -------------  -----------  -----------------------  ----------------------
    Distri Norte   distri-norte admin@distri-norte.com   kiosco@distri-norte.com
    Distri Sur     distri-sur   admin@distri-sur.com     kiosco@distri-sur.com
"""
from decimal import Decimal

from sqlalchemy import select

import app.models  # noqa: F401  (registra todos los modelos)
import app.analytics.models.analytics_catalog_event_model  # noqa: F401
import app.analytics.models.analytics_client_daily_model  # noqa: F401
import app.analytics.models.analytics_daily_model  # noqa: F401
import app.analytics.models.analytics_product_daily_model  # noqa: F401
import app.analytics.models.analytics_sales_rep_daily_model  # noqa: F401
import app.analytics.models.analytics_zone_product_daily_model  # noqa: F401
from app.db.base import SessionLocal
from app.db.tenant_context import tenant_scope, unscoped
from app.models.client_model import Client
from app.models.product_model import Product
from app.models.tenant_model import Tenant
from app.schemas.client_schema import ClientCreate
from app.schemas.product_schema import ProductCreateAdmin
from app.schemas.tenant_schema import TenantProvision
from app.services.client_service import ClientService
from app.services.product_service import ProductService
from app.services.tenant_service import TenantService

PASSWORD = "demo1234"

DEMO_TENANTS = [
    {"name": "Distri Norte", "slug": "distri-norte", "products": [
        ("NOR-001", "Alfajor Triple", "Terrabusi", "Golosinas", "100", "160", 120),
        ("NOR-002", "Chocolate Aguila 150g", "Aguila", "Chocolates", "250", "390", 60),
        ("NOR-003", "Galletitas Oreo", "Oreo", "Galletitas", "180", "270", 80),
    ]},
    {"name": "Distri Sur", "slug": "distri-sur", "products": [
        ("SUR-001", "Alfajor Triple", "Terrabusi", "Golosinas", "105", "165", 90),
        ("SUR-002", "Yerba Mate 1kg", "Taragüí", "Almacén", "900", "1350", 40),
        ("SUR-003", "Gaseosa Cola 2.25L", "Coca-Cola", "Bebidas", "700", "1050", 70),
    ]},
]


def main() -> None:
    db = SessionLocal()
    try:
        for spec in DEMO_TENANTS:
            slug = spec["slug"]

            with unscoped(db):
                tenant = db.scalar(select(Tenant).where(Tenant.slug == slug))
            if tenant is None:
                tenant = TenantService(db).provision(
                    TenantProvision(
                        name=spec["name"],
                        slug=slug,
                        email=f"contacto@{slug}.com",
                        admin_email=f"admin@{slug}.com",
                        admin_password=PASSWORD,
                        admin_name=f"Admin {spec['name']}",
                    )
                )
                print(f"+ tenant '{slug}' creado")
            else:
                print(f"= tenant '{slug}' ya existía")

            # Todo lo que sigue se crea DENTRO del tenant (la sesión estampa tenant_id).
            with tenant_scope(db, tenant.id):
                products = ProductService(db)
                for sku, name, brand, category, cost, price, stock in spec["products"]:
                    if products.repo.get_product_by_sku(sku):
                        continue
                    products.create_product(
                        product_in=ProductCreateAdmin(
                            name=name, brand=brand, category=category, sku=sku,
                            unit_cost=Decimal(cost), unit_price=Decimal(price),
                            stock_current=stock, stock_min=10,
                            image_url="https://example.com/placeholder.jpg",
                        )
                    )

                email = f"kiosco@{slug}.com"
                if not db.scalar(select(Client).where(Client.email == email)):
                    ClientService(db).create_client(
                        ClientCreate(
                            name=f"Kiosco de {spec['name']}",
                            client_type="kiosco",
                            email=email,
                            password=PASSWORD,
                            tax_id="20123456786",
                            phone="1155550000",
                        )
                    )
                db.commit()
            print(f"  productos y cliente de '{slug}' listos")

        print("\nListo. Contraseña de todos los usuarios demo:", PASSWORD)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
