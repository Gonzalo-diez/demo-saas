import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.cors import TenantAwareCORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.core.scheduler import scheduler, setup_scheduler
from app.db.session import SessionLocal
from app.api.routes.client_route import router as client_router
from app.api.routes.dashboard_route import router as dashboard_router
from app.api.routes.inventory_movement_route import router as inventory_movement_router
from app.api.routes.client_account_movement_route import router as client_account_movement_router
from app.api.routes.supplier_account_movement_route import router as supplier_account_movement_router
from app.api.routes.order_route import router as order_router
from app.api.routes.product_route import router as product_router
from app.api.routes.product_purchase_route import router as product_purchase_router
from app.api.routes.category_route import router as category_router
from app.api.routes.purchase_invoice_route import router as purchase_invoice_router
from app.api.routes.sales_invoice_route import router as sales_invoice_router
from app.api.routes.purchase_quote_route import router as purchase_quote_router
from app.api.routes.sales_quote_route import router as sales_quote_router
from app.api.routes.sales_rep_route import router as sales_rep_router
from app.api.routes.supplier_route import router as supplier_router
from app.api.routes.upload_route import router as upload_router
from app.api.routes.analytics_route import router as analytics_router
from app.api.routes.whatsapp_webhook_route import router as whatsapp_webhook_router
from app.api.routes.account_ledger_route import router as account_ledger_router
from app.api.routes.account_ledger_import_route import router as account_ledger_import_router
from app.api.routes.check_route import router as check_router
from app.api.routes.tenant_route import router as tenant_router
from app.api.routes.admin_route import router as admin_router
from app.api.routes.notification_route import router as notification_router
from app.core.init_admin import create_first_superuser, create_first_tenant
from app.core.init_platform_admin import create_first_platform_admin
import app.db.events

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando lifespan de la aplicación...")
    db = SessionLocal()
    try:
        # Cada paso va aparte: si falla el admin de plataforma no debe
        # impedir que se cree el tenant inicial (ni al revés).
        for step in (create_first_platform_admin, create_first_tenant, create_first_superuser):
            try:
                step(db)
            except Exception as e:
                db.rollback()
                print(f"Fallo crítico en {step.__name__}: {e}")
    finally:
        db.close()
        
    setup_scheduler()
    scheduler.start()
    print("Scheduler iniciado con trabajos programados.")
    
    yield
    
    scheduler.shutdown()
    print("Scheduler detenido.")
    
    print("Apagando aplicación...")
    
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    TenantAwareCORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sales_rep_router, prefix="/api")
app.include_router(product_router, prefix="/api")
app.include_router(product_purchase_router, prefix="/api")
app.include_router(category_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(client_router, prefix="/api")
app.include_router(supplier_router, prefix="/api")
app.include_router(order_router, prefix="/api")
app.include_router(purchase_invoice_router, prefix="/api")
app.include_router(sales_invoice_router, prefix="/api")
app.include_router(purchase_quote_router, prefix="/api")
app.include_router(sales_quote_router, prefix="/api")
app.include_router(inventory_movement_router, prefix="/api")
app.include_router(client_account_movement_router, prefix="/api")
app.include_router(supplier_account_movement_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(whatsapp_webhook_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(account_ledger_router, prefix="/api")
app.include_router(account_ledger_import_router, prefix="/api")
app.include_router(check_router, prefix="/api")
app.include_router(notification_router, prefix="/api")
app.include_router(tenant_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
