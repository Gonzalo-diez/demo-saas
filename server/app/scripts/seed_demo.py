"""
Seed de la demo SaaS: crea dos distribuidoras (tenants) con su administrador,
sus propias categorías (algunas públicas y otras no), productos (publicados o
no) y un cliente B2B cada una. Es idempotente: se puede correr
varias veces.

Uso (con las migraciones ya aplicadas):

    python -m app.scripts.seed_demo

Credenciales que deja (contraseña de todos: demo1234):

    distribuidora  slug         dominio de la tienda     admin                    cliente B2B
    -------------  -----------  -----------------------  -----------------------  ----------------------
    Distri Norte   distri-norte distri-norte.localhost   admin@distri-norte.com   kiosco@distri-norte.com
    Distri Sur     distri-sur   distri-sur.localhost     admin@distri-sur.com     kiosco@distri-sur.com
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
from app.schemas.category_schema import CategoryCreate
from app.schemas.client_schema import ClientCreate
from app.schemas.product_schema import ProductCreateAdmin
from app.schemas.tenant_schema import TenantProvision
from app.repositories.category_repository import CategoryRepository
from app.services.category_service import CategoryService
from app.services.client_service import ClientService
from app.services.product_service import ProductService
from app.services.tenant_service import TenantService

PASSWORD = "demo1234"

# Cada distribuidora arma SUS categorías (nombre, pública?) y productos
# (sku, nombre, marca, categoría, costo, precio, stock, publicado?).
DEMO_TENANTS = [
    {
        "name": "Distri Norte", "slug": "distri-norte",
        "categories": [("Golosinas", True), ("Chocolates", True), ("Insumos internos", False)],
        "products": [
            ("NOR-001", "Alfajor Triple", "Terrabusi", "Golosinas", "100", "160", 120, True),
            ("NOR-002", "Chocolate Aguila 150g", "Aguila", "Chocolates", "250", "390", 60, True),
            ("NOR-003", "Bolsas de embalaje", "Genérica", "Insumos internos", "50", "80", 500, True),
        ],
    },
    {
        "name": "Distri Sur", "slug": "distri-sur",
        "categories": [("Golosinas", True), ("Almacén", True), ("Bebidas", False)],
        "products": [
            ("SUR-001", "Alfajor Triple", "Terrabusi", "Golosinas", "105", "165", 90, True),
            ("SUR-002", "Yerba Mate 1kg", "Taragüí", "Almacén", "900", "1350", 40, False),
            ("SUR-003", "Gaseosa Cola 2.25L", "Coca-Cola", "Bebidas", "700", "1050", 70, True),
        ],
    },
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
                        # En desarrollo *.localhost resuelve a 127.0.0.1: la tienda de
                        # cada distribuidora se abre en http://<slug>.localhost:3000
                        domain=f"{slug}.localhost",
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
                categories = CategoryService(db)
                category_ids: dict[str, int] = {}
                for cat_name, cat_public in spec["categories"]:
                    existing = CategoryRepository(db).get_by_name(cat_name)
                    category = existing or categories.create_category(
                        CategoryCreate(
                            name=cat_name,
                            is_public=cat_public,
                            # Una categoría pública necesita imagen (como un producto).
                            image_url="https://example.com/categoria.jpg" if cat_public else None,
                        )
                    )
                    category_ids[cat_name] = category.id

                products = ProductService(db)
                for sku, name, brand, category, cost, price, stock, published in spec["products"]:
                    if products.repo.get_product_by_sku(sku):
                        continue
                    products.create_product(
                        product_in=ProductCreateAdmin(
                            name=name, brand=brand, category_id=category_ids[category], sku=sku,
                            unit_cost=Decimal(cost), unit_price=Decimal(price),
                            stock_current=stock, stock_min=10, is_public=published,
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
            print(f"  categorías, productos y cliente de '{slug}' listos")

        print("\nListo. Contraseña de todos los usuarios demo:", PASSWORD)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
