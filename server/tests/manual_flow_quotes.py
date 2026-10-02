import os, sys, glob, importlib, logging
os.environ["DATABASE_URL"]="postgresql://postgres:pw@localhost/chocotest"
sys.path.insert(0, os.getcwd())
import app.models
for f in glob.glob("app/analytics/models/*.py"):
    importlib.import_module(f[:-3].replace("/","."))
import app.db.events
from app.db.base import Base, engine, SessionLocal
engine.echo = False
logging.disable(logging.CRITICAL)
Base.metadata.create_all(engine)

from decimal import Decimal
from datetime import date, timedelta
from fastapi import HTTPException
import app.services.email_service as email_service
import app.services.whatsapp_service as wa
sent = []
for name in dir(email_service):
    if name.startswith("send_"):
        setattr(email_service, name, lambda *a, **k: sent.append(1))
for name in dir(wa):
    if name.startswith("send_"):
        setattr(wa, name, lambda *a, **k: None)
# el hook de analytics corre jobs post-commit; lo neutralizamos (no es lo que probamos)
import app.db.events.sales_invoice_events as ev
ev._flush_pending_aggregations = lambda s: None

from app.models import SalesRep, Client, ClientBranch, Product, SalesQuote, SalesInvoice, ClientAccountMovement, Order
from app.services.order_service import OrderService
from app.services.sales_quote_service import SalesQuoteService
from app.services.client_account_movement_service import ClientAccountMovementService
from app.schemas.order_schema import OrderCreateShop, OrderItemCreate, OrderResponse
from app.schemas.sales_quote_schema import SalesQuoteResponse, SalesQuoteCreate, SalesQuoteItemCreate
from app.schemas.account_movement_schema import ClientPaymentCreate, ClientPaymentAllocationItem
from app.services.sales_quote_pdf_service import build_sales_quote_pdf

db = SessionLocal()
rep = SalesRep(name="Admin", email="a@a.com", hashed_password="x", is_superuser=True); db.add(rep)
client = Client(name="Kiosco Uno", client_type="kiosco", tax_id="20123456786", email="k@k.com", phone="1155550000", hashed_password="x"); db.add(client)
db.flush()
branch = ClientBranch(client_id=client.id, name="Sucursal Centro", address="Calle 1", city="Corrientes"); db.add(branch)
p1 = Product(name="Alfajor", name_normalized="alfajor", brand="Terrabusi", brand_normalized="terrabusi", category="Sin Clasificar", category_normalized="sin clasificar", slug="alfajor", unit_price=Decimal("100"), unit_cost=Decimal("60"), stock_current=100, is_active=True, sku="A1")
p2 = Product(name="Chocolate", name_normalized="chocolate", brand="Aguila", brand_normalized="aguila", category="Sin Clasificar", category_normalized="sin clasificar", slug="choco", unit_price=Decimal("250"), unit_cost=Decimal("150"), stock_current=50, is_active=True, sku="C1")
db.add_all([p1, p2]); db.commit()

def new_order(doc):
    svc = OrderService(db)
    o = svc.create_order_shop(obj_in=OrderCreateShop(
        customer_name="Kiosco Uno", customer_phone="1155550000", customer_email="k@k.com",
        client_branch_id=branch.id, delivery_type="delivery", delivery_address="Calle 1", delivery_city="Corrientes",
        preferred_delivery_date=date.today()+timedelta(days=2), document_type=doc,
        items=[OrderItemCreate(product_id=p1.id, quantity=2), OrderItemCreate(product_id=p2.id, quantity=1)]),
        current_client=client)
    return o  # total = 450

def bal():
    db.expire_all(); return Decimal(db.get(Client, client.id).current_balance)
def stock():
    db.expire_all(); return db.get(Product, p1.id).stock_current, db.get(Product, p2.id).stock_current
def ok(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond: FAILS.append(msg)
FAILS = []

# ---------- A) pedido con presupuesto
o = new_order("sales_quote")
ok(o.document_type == "sales_quote", "checkout guarda document_type=sales_quote")
svc = OrderService(db)
svc.update_order_status(o.id, "confirmed", rep); db.commit()
ok(stock() == (98, 49), f"confirmed consumió stock {stock()}")
svc.update_order_status(o.id, "preparing", rep); db.commit()
db.expire_all()
q = db.query(SalesQuote).filter_by(order_id=o.id).one()
ok(q.status == "approved" and q.total_amount == Decimal("450.00") and q.total_cost == Decimal("270.00") and q.margin_amount == Decimal("180.00"), f"presupuesto generado approved total={q.total_amount} costo={q.total_cost} margen={q.margin_amount}")
ok(q.quote_number.startswith("PRE-0001-") and q.client_branch_id == branch.id and q.customer_tax_id == "20123456786", f"numero {q.quote_number}, sucursal y cuit copiados")
ok(db.query(SalesInvoice).filter_by(order_id=o.id).count() == 0, "NO se generó remito")
ok(bal() == Decimal("450.00"), f"deuda registrada en cuenta corriente = {bal()}")
mv = db.query(ClientAccountMovement).filter_by(reference_type="sales_quote", reference_id=q.id).one()
ok(mv.movement_type == "invoice", "movimiento invoice con reference_type=sales_quote")
ok(db.get(Order, o.id).invoice_generated is True, "order.invoice_generated=True")
OrderResponse.model_validate(svc.get_order(o.id)); r = OrderResponse.model_validate(svc.get_order(o.id))
ok(r.sales_quote is not None and r.sales_quote.id == q.id and r.document_type == "sales_quote", "OrderResponse expone document_type y sales_quote")
sr = SalesQuoteResponse.model_validate(SalesQuoteService(db).get_by_id(q.id))
ok(sr.client_name == "Kiosco Uno" and sr.client_tax_id == "20123456786" and sr.order_id == o.id, "SalesQuoteResponse mantiene client_name/client_tax_id")
ok(len(build_sales_quote_pdf(SalesQuoteService(db).get_by_id(q.id))) > 500, "PDF del presupuesto se genera")

cam = ClientAccountMovementService(db)
resp = cam.register_payment(client.id, ClientPaymentCreate(amount=Decimal("200"), payment_method="efectivo",
        allocations=[ClientPaymentAllocationItem(invoice_id=q.id, amount=Decimal("200"), document_type="sales_quote")]), rep); db.commit()
db.expire_all(); q = db.get(SalesQuote, q.id)
ok(q.payment_status == "partial" and q.paid_amount == Decimal("200.00") and bal() == Decimal("250.00"), f"cobro parcial imputado al presupuesto: {q.payment_status}, saldo {bal()}")
ok(resp.allocations[0].document_type == "sales_quote" and resp.allocations[0].invoice_number == q.quote_number, "respuesta del cobro muestra la imputación al presupuesto")
page = cam.get_movements(client_id=client.id)
ref = [m for m in page["items"] if m.reference_type == "sales_quote"][0].reference_summary
ok(ref is not None and ref.document_type == "sales_quote" and ref.invoice_number == q.quote_number, "listado de movimientos enriquece la referencia a presupuesto")
aging = cam.get_aging_summary()
ok(aging.total_pending == Decimal("250.00"), f"aging incluye el presupuesto: {aging.total_pending}")
try:
    cam.register_payment(client.id, ClientPaymentCreate(amount=Decimal("300"), payment_method="efectivo",
        allocations=[ClientPaymentAllocationItem(invoice_id=q.id, amount=Decimal("300"), document_type="sales_quote")]), rep)
    ok(False, "debería rechazar sobre-imputación")
except HTTPException as e:
    ok(e.status_code == 400, "rechaza imputar más que el saldo del presupuesto")
    db.rollback()
try:
    svc.update_order_status(o.id, "cancelled", rep)
    ok(False, "debería bloquear cancelar con cobros")
except HTTPException as e:
    ok(e.status_code == 400, "no deja cancelar el pedido si el presupuesto ya tiene cobros")
    db.rollback()
try:
    SalesQuoteService(db).update_status(q.id, "rejected", rep)
    ok(False, "debería bloquear cambio manual")
except HTTPException as e:
    ok(e.status_code == 400, "estado de presupuesto de pedido no se cambia a mano")
    db.rollback()

# ---------- B) presupuesto de pedido cancelado sin cobros
b0 = bal(); s0 = stock()
o2 = new_order("sales_quote")
svc.update_order_status(o2.id, "confirmed", rep); svc.update_order_status(o2.id, "preparing", rep); db.commit()
ok(bal() == b0 + Decimal("450.00"), "segundo pedido suma deuda")
svc.update_order_status(o2.id, "cancelled", rep); db.commit()
db.expire_all()
q2 = db.query(SalesQuote).filter_by(order_id=o2.id).one()
ok(q2.status == "cancelled" and bal() == b0 and stock() == s0, f"cancelar pedido: presupuesto={q2.status}, saldo revertido={bal()}, stock repuesto={stock()}")
rev = db.query(ClientAccountMovement).filter_by(reference_type="sales_quote", reference_id=q2.id, movement_type="invoice_reversal").count()
ok(rev == 1, "movimiento invoice_reversal registrado")

# ---------- C) regresión: pedido con remito (default)
o3 = new_order("sales_invoice")
b1 = bal()
svc.update_order_status(o3.id, "confirmed", rep); svc.update_order_status(o3.id, "preparing", rep); db.commit()
db.expire_all()
inv = db.query(SalesInvoice).filter_by(order_id=o3.id).one()
ok(inv.status == "confirmed" and db.query(SalesQuote).filter_by(order_id=o3.id).count() == 0, "pedido con remito sigue generando remito confirmado (sin presupuesto)")
ok(bal() == b1 + Decimal("450.00"), "remito registra deuda como antes")
cam.register_payment(client.id, ClientPaymentCreate(amount=Decimal("450"), payment_method="efectivo",
    allocations=[ClientPaymentAllocationItem(invoice_id=inv.id, amount=Decimal("450"))]), rep); db.commit()
db.expire_all(); ok(db.get(SalesInvoice, inv.id).payment_status == "paid", "cobro imputado a remito (default document_type) sigue funcionando")

# ---------- D) cotización suelta
qs = SalesQuoteService(db)
manual = qs.create(SalesQuoteCreate(client_name="CONSUMIDOR FINAL", quote_number="M-1", quote_date=date.today(), payment_method="EFECTIVO",
        items=[SalesQuoteItemCreate(product_id=p1.id, product_name="Alfajor", quantity=3, unit_price=Decimal("110")),
               SalesQuoteItemCreate(product_name="Item libre", quantity=1, unit_price=Decimal("50"))]), rep); db.commit()
ok(manual.order_id is None and manual.total_amount == Decimal("375.00") and manual.total_cost is None and manual.customer_name == "CONSUMIDOR FINAL", "cotización suelta: total 375, costo desconocido -> None")
b2 = bal(); qs.update_status(manual.id, "approved", rep); db.commit()
ok(bal() == b2, "aprobar cotización suelta NO toca cuenta corriente")
try:
    cam.register_payment(client.id, ClientPaymentCreate(amount=Decimal("10"), payment_method="efectivo",
        allocations=[ClientPaymentAllocationItem(invoice_id=manual.id, amount=Decimal("10"), document_type="sales_quote")]), rep)
    ok(False, "no debería aceptar cobro sobre cotización suelta")
except HTTPException as e:
    ok(e.status_code == 400, "rechaza cobros sobre una cotización suelta"); db.rollback()
ok(SalesQuoteResponse.model_validate(qs.get_by_id(manual.id)).client_name == "CONSUMIDOR FINAL", "respuesta de cotización suelta OK")

print("\nRESULT:", "TODO OK" if not FAILS else f"{len(FAILS)} FALLAS: {FAILS}")
