from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from app.db.base import Base
from app.models.sales_rep_model import SalesRep
from app.models.client_model import Client
from app.models.client_branch_model import ClientBranch
from app.models.client_payment_allocation_model import ClientPaymentAllocation
from app.models.client_account_movement_model import ClientAccountMovement
from app.models.category_model import Category
from app.models.product_model import Product
from app.models.order_model import Order
from app.models.order_item_model import OrderItem
from app.models.inventory_movement_model import InventoryMovement
from app.models.purchase_invoice_model import PurchaseInvoice
from app.models.purchase_invoice_item_model import PurchaseInvoiceItem
from app.models.sales_invoice_model import SalesInvoice
from app.models.sales_invoice_item_model import SalesInvoiceItem
from app.models.sales_invoice_payment_model import SalesInvoicePayment
from app.models.supplier_model import Supplier
from app.models.supplier_account_movement_model import SupplierAccountMovement
from app.models.supplier_payment_allocation_model import SupplierPaymentAllocation
from app.models.inventory_movement_model import InventoryMovement
from app.models.purchase_quote_model import PurchaseQuote
from app.models.purchase_quote_item_model import PurchaseQuoteItem
from app.models.sales_quote_model import SalesQuote
from app.models.sales_quote_item_model import SalesQuoteItem
from app.models.sales_quote_payment_model import SalesQuotePayment
from app.models.check_model import Check
from app.models.tenant_model import Tenant
from app.models.admin_model import Admin
from app.models.mixin_model import TenantMixin
from app.models.notification_model import Notification
from app.analytics.models.analytics_daily_model import AnalyticsDaily
from app.analytics.models.analytics_product_daily_model import AnalyticsProductDaily
from app.analytics.models.analytics_sales_rep_daily_model import AnalyticsSalesRepDaily
from app.analytics.models.analytics_zone_product_daily_model import AnalyticsZoneProductDaily
from app.analytics.models.analytics_catalog_event_model import AnalyticsCatalogEvent
from app.analytics.models.analytics_client_daily_model import AnalyticsClientDaily

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# metadata para autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()