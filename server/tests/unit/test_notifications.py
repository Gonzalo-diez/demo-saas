"""
test_notifications.py — Notificaciones de stock (bajo / cerca del mínimo /
sin stock) y de cheques (recibidos y emitidos).

Las reglas (qué estado corresponde) se prueban como funciones puras; el
resto con BD sqlite real: enganche en tiempo real, barrido diario, ciclo
de vida (alta, escalada, resolución) y la API de lectura.
"""
import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.core.security import get_password_hash
from app.models.client_model import Client
from app.models.notification_model import Notification
from app.models.product_model import Product
from app.models.supplier_model import Supplier
from app.repositories.notification_repository import NotificationRepository
from app.schemas.check_schema import (
    CheckRejectRequest,
    IssuedCheckCreate,
    ReceivedCheckCreate,
)
from app.services.check_service import CheckService
from app.services.inventory_movement_service import InventoryMovementService
from app.services.notification_alert_service import (
    NotificationAlertService,
    format_ars,
    get_check_alert_type,
    get_stock_alert_type,
    today_local,
)
from app.services.notification_service import NotificationService


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _make_product(db, *, stock=20, stock_min=10, is_active=True, name=None):
    unique = uuid.uuid4().hex[:8]
    name = name or f"Producto Notif {unique}"
    product = Product(
        name=name,
        name_normalized=name.lower(),
        brand="Marca",
        brand_normalized="marca",
        category="pilas",
        category_normalized="pilas",
        slug=f"producto-notif-{unique}",
        unit_price=Decimal("100.00"),
        unit_cost=Decimal("50.00"),
        stock_current=stock,
        stock_min=stock_min,
        sku=f"SKU-N-{unique}",
        is_active=is_active,
        status="ACTIVE" if is_active else "DRAFT",
    )
    db.add(product)
    db.flush()
    return product


def _make_client(db, name="Cliente Notif"):
    client = Client(
        name=name,
        client_type="B2B",
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
    )
    db.add(client)
    db.flush()
    return client


def _make_supplier(db, name="Proveedor Notif"):
    supplier = Supplier(name=name, is_active=True)
    db.add(supplier)
    db.flush()
    return supplier


def _active(db, dedup_key):
    return NotificationRepository(db).get_active_by_dedup_key(dedup_key)


def _all_for(db, dedup_key):
    return db.query(Notification).filter(Notification.dedup_key == dedup_key).all()


def _move(db, product, movement_type, quantity):
    InventoryMovementService(db).apply_movement(
        product_id=product.id,
        movement_type=movement_type,
        quantity=Decimal(quantity),
        reference_type="manual_adjustment",
    )
    db.flush()


def _received_check(db, sales_rep, client, *, payment_in, due_in, amount="1500.00", number=None):
    today = today_local()
    return CheckService(db).register_received(
        client.id,
        ReceivedCheckCreate(
            check_number=number or uuid.uuid4().hex[:6],
            amount=Decimal(amount),
            issue_date=today - timedelta(days=60),
            payment_date=today + timedelta(days=payment_in),
            due_date=today + timedelta(days=due_in),
        ),
        sales_rep,
    )


def _issued_check(db, sales_rep, supplier, *, payment_in, due_in, amount="2000.00", number=None):
    today = today_local()
    return CheckService(db).register_issued(
        supplier.id,
        IssuedCheckCreate(
            check_number=number or uuid.uuid4().hex[:6],
            amount=Decimal(amount),
            issue_date=today - timedelta(days=60),
            payment_date=today + timedelta(days=payment_in),
            due_date=today + timedelta(days=due_in),
        ),
        sales_rep,
    )


# ----------------------------------------------------------------------
# Reglas puras
# ----------------------------------------------------------------------

class TestStockRule:
    @pytest.mark.parametrize(
        "stock, minimum, expected",
        [
            (0, 0, "stock_out"),
            (0, 10, "stock_out"),
            (1, 10, "stock_low"),
            (10, 10, "stock_low"),
            (11, 10, "stock_near_min"),
            (12, 10, "stock_near_min"),
            (13, 10, None),
            (50, 10, None),
            (1, 0, None),       # sin mínimo cargado: solo avisa cuando no hay nada
            (500, 0, None),
        ],
    )
    def test_levels_with_20_percent_margin(self, stock, minimum, expected):
        assert get_stock_alert_type(stock, minimum, margin_percent=20) == expected

    def test_inactive_products_never_alert(self):
        assert get_stock_alert_type(0, 10, margin_percent=20, is_active=False) is None

    def test_margin_zero_only_alerts_at_or_below_minimum(self):
        assert get_stock_alert_type(11, 10, margin_percent=0) is None
        assert get_stock_alert_type(10, 10, margin_percent=0) == "stock_low"


class TestCheckRule:
    TODAY = date(2026, 9, 30)

    def _type(self, *, status="pendiente", payment_in, due_in, days_before=3):
        return get_check_alert_type(
            status=status,
            payment_date=self.TODAY + timedelta(days=payment_in),
            due_date=self.TODAY + timedelta(days=due_in),
            today=self.TODAY,
            days_before=days_before,
        )

    def test_overdue(self):
        assert self._type(payment_in=-30, due_in=-1) == "check_overdue"

    def test_due_today_is_due_soon_not_overdue(self):
        assert self._type(payment_in=-30, due_in=0) == "check_due_soon"

    def test_due_within_window(self):
        assert self._type(payment_in=-30, due_in=3) == "check_due_soon"

    def test_payable_when_payment_date_reached_and_due_is_far(self):
        assert self._type(payment_in=0, due_in=30) == "check_payable"
        assert self._type(payment_in=-10, due_in=30) == "check_payable"

    def test_upcoming_within_window(self):
        assert self._type(payment_in=2, due_in=30) == "check_upcoming"

    def test_nothing_when_everything_is_far(self):
        assert self._type(payment_in=10, due_in=40) is None

    def test_due_soon_wins_over_payable(self):
        assert self._type(payment_in=-5, due_in=2) == "check_due_soon"

    @pytest.mark.parametrize("status", ["depositado", "acreditado", "rechazado"])
    def test_only_pending_checks_alert(self, status):
        assert self._type(status=status, payment_in=-30, due_in=-1) is None


def test_format_ars():
    assert format_ars(Decimal("1234.5")) == "$ 1.234,50"
    assert format_ars(Decimal("1500000")) == "$ 1.500.000,00"
    assert format_ars(Decimal("0.99")) == "$ 0,99"


# ----------------------------------------------------------------------
# Stock en tiempo real (enganchado en apply_movement)
# ----------------------------------------------------------------------

class TestStockNotifications:
    def test_healthy_stock_creates_nothing(self, db):
        product = _make_product(db, stock=50, stock_min=10)
        _move(db, product, "sale", "5")
        assert _all_for(db, f"stock:{product.id}") == []

    def test_sale_walks_through_near_low_out_then_restock_resolves(self, db):
        product = _make_product(db, stock=20, stock_min=10)
        key = f"stock:{product.id}"

        _move(db, product, "sale", "8")  # 12 -> cerca del mínimo
        assert _active(db, key).type == "stock_near_min"
        assert _active(db, key).severity == "info"

        _move(db, product, "sale", "3")  # 9 -> bajo
        assert _active(db, key).type == "stock_low"
        assert _active(db, key).severity == "warning"

        _move(db, product, "sale", "9")  # 0 -> sin stock
        notification = _active(db, key)
        assert notification.type == "stock_out"
        assert notification.severity == "critical"
        assert product.name in notification.title
        assert notification.data["stock_current"] == 0

        _move(db, product, "purchase", "100")  # repone
        assert _active(db, key) is None

        # Sigue siendo una sola fila (se fue actualizando) y quedó resuelta.
        rows = _all_for(db, key)
        assert len(rows) == 1
        assert rows[0].resolved_at is not None

    def test_same_level_does_not_duplicate(self, db):
        product = _make_product(db, stock=12, stock_min=10)
        key = f"stock:{product.id}"
        NotificationAlertService(db).sync_product_stock(product)
        _move(db, product, "sale", "1")  # 11, sigue cerca del mínimo
        assert len(_all_for(db, key)) == 1

    def test_escalation_marks_unread_again_but_deescalation_does_not(self, db, sales_rep):
        product = _make_product(db, stock=11, stock_min=10)
        key = f"stock:{product.id}"
        NotificationAlertService(db).sync_product_stock(product)
        notification = _active(db, key)

        service = NotificationService(db)
        service.mark_read(notification.id, sales_rep.id)
        assert service.get_unread_count(sales_rep.id)["unread_count"] == 0

        _move(db, product, "sale", "5")  # 6 -> bajo: empeoró
        assert service.get_unread_count(sales_rep.id)["unread_count"] == 1

        service.mark_read(notification.id, sales_rep.id)
        _move(db, product, "purchase", "5")  # 11 -> cerca del mínimo: mejoró
        assert _active(db, key).type == "stock_near_min"
        assert service.get_unread_count(sales_rep.id)["unread_count"] == 0

    def test_inactive_product_does_not_alert(self, db):
        product = _make_product(db, stock=5, stock_min=10, is_active=False)
        _move(db, product, "sale", "5")
        assert _all_for(db, f"stock:{product.id}") == []

    def test_changing_the_minimum_recalculates_alert(self, db):
        from app.services.product_service import ProductService
        from app.schemas.product_schema import ProductUpdate

        product = _make_product(db, stock=15, stock_min=10)
        # update_product recalcula is_active según si el producto está completo
        product.image_url = "https://img.example.com/producto.jpg"
        db.flush()
        key = f"stock:{product.id}"
        assert _active(db, key) is None

        ProductService(db).update_product(
            product_id=product.id, obj_in=ProductUpdate(stock_min=20)
        )
        assert _active(db, key).type == "stock_low"

    def test_a_failing_notification_never_breaks_the_sale(self, db, monkeypatch):
        product = _make_product(db, stock=5, stock_min=10)

        def boom(self, *args, **kwargs):
            raise RuntimeError("falló el aviso")

        monkeypatch.setattr(NotificationAlertService, "sync_product_stock", boom)

        _move(db, product, "sale", "2")  # no debe levantar
        db.refresh(product)
        assert product.stock_current == 3


class TestStockFullSync:
    def test_sync_all_stock_is_idempotent_and_resolves_stale(self, db):
        out = _make_product(db, stock=0, stock_min=5)
        low = _make_product(db, stock=3, stock_min=5)
        near = _make_product(db, stock=6, stock_min=5)
        healthy = _make_product(db, stock=100, stock_min=5)
        inactive = _make_product(db, stock=0, stock_min=5, is_active=False)
        service = NotificationAlertService(db)

        first = service.sync_all_stock()
        assert first["active"] == 3
        types = {
            p.id: (_active(db, f"stock:{p.id}") or Notification(type=None)).type
            for p in (out, low, near, healthy, inactive)
        }
        assert types[out.id] == "stock_out"
        assert types[low.id] == "stock_low"
        assert types[near.id] == "stock_near_min"
        assert types[healthy.id] is None
        assert types[inactive.id] is None

        service.sync_all_stock()  # segunda pasada: no duplica
        total = db.query(Notification).filter(Notification.category == "stock").count()
        assert total == 3

        low.stock_current = 50  # se repuso por fuera del flujo normal
        db.flush()
        second = service.sync_all_stock()
        assert second["resolved"] == 1
        assert _active(db, f"stock:{low.id}") is None


# ----------------------------------------------------------------------
# Cheques
# ----------------------------------------------------------------------

class TestCheckNotifications:
    def test_received_check_due_soon_then_deposit_resolves(self, db, sales_rep):
        client = _make_client(db, "Kiosco Pérez")
        check = _received_check(db, sales_rep, client, payment_in=-5, due_in=2, amount="1500.00", number="0001")
        key = f"check:{check.id}"

        notification = _active(db, key)
        assert notification.type == "check_due_soon"
        assert notification.category == "check"
        assert notification.entity_type == "check" and notification.entity_id == check.id
        assert "Kiosco Pérez" in notification.message
        assert "$ 1.500,00" in notification.message
        assert notification.data["direction"] == "received"

        CheckService(db).mark_as_deposited(check.id)
        assert _active(db, key) is None

    def test_received_check_overdue(self, db, sales_rep):
        client = _make_client(db)
        check = _received_check(db, sales_rep, client, payment_in=-20, due_in=-1)
        notification = _active(db, f"check:{check.id}")
        assert notification.type == "check_overdue"
        assert notification.severity == "critical"

    def test_issued_check_payable_asks_to_secure_funds(self, db, sales_rep):
        supplier = _make_supplier(db, "Distribuidora Sur")
        check = _issued_check(db, sales_rep, supplier, payment_in=0, due_in=30, amount="2000.00")
        notification = _active(db, f"check:{check.id}")
        assert notification.type == "check_payable"
        assert "Distribuidora Sur" in notification.message
        assert "fondos" in notification.message
        assert notification.data["direction"] == "issued"

    def test_issued_check_upcoming(self, db, sales_rep):
        supplier = _make_supplier(db)
        check = _issued_check(db, sales_rep, supplier, payment_in=2, due_in=30)
        assert _active(db, f"check:{check.id}").type == "check_upcoming"

    def test_far_away_check_has_no_notification(self, db, sales_rep):
        client = _make_client(db)
        check = _received_check(db, sales_rep, client, payment_in=20, due_in=50)
        assert _all_for(db, f"check:{check.id}") == []

    def test_credit_resolves_notification(self, db, sales_rep):
        client = _make_client(db)
        check = _received_check(db, sales_rep, client, payment_in=-5, due_in=-1)
        assert _active(db, f"check:{check.id}") is not None

        CheckService(db).credit(check.id, sales_rep)
        assert _active(db, f"check:{check.id}") is None

    def test_reject_closes_expiry_alert_and_creates_rejected_event(self, db, sales_rep):
        client = _make_client(db, "Almacén Norte")
        check = _received_check(db, sales_rep, client, payment_in=-5, due_in=1, number="9999")

        CheckService(db).reject(check.id, CheckRejectRequest(notes="sin fondos"))

        assert _active(db, f"check:{check.id}") is None
        rejected = _active(db, f"check_rejected:{check.id}")
        assert rejected.type == "check_rejected"
        assert rejected.severity == "critical"
        assert "Almacén Norte" in rejected.message

    def test_sync_all_checks_picks_up_date_changes_and_is_idempotent(self, db, sales_rep):
        client = _make_client(db)
        check = _received_check(db, sales_rep, client, payment_in=20, due_in=50)
        assert _all_for(db, f"check:{check.id}") == []

        service = NotificationAlertService(db)
        # Pasan los días: el cheque entra en su ventana de vencimiento.
        future = today_local() + timedelta(days=48)
        first = service.sync_all_checks(today=future)
        assert first["active"] == 1
        assert _active(db, f"check:{check.id}").type == "check_due_soon"

        service.sync_all_checks(today=future)
        assert len(_all_for(db, f"check:{check.id}")) == 1

        # Y si vence sin que nadie lo toque, escala a vencido y vuelve a no leído.
        overdue_day = today_local() + timedelta(days=52)
        service.sync_all_checks(today=overdue_day)
        assert _active(db, f"check:{check.id}").type == "check_overdue"

    def test_sync_all_checks_resolves_alerts_of_checks_no_longer_pending(self, db, sales_rep):
        client = _make_client(db)
        check = _received_check(db, sales_rep, client, payment_in=-5, due_in=1)
        assert _active(db, f"check:{check.id}") is not None

        check.status = "acreditado"  # cambio por fuera del flujo normal
        db.flush()
        NotificationAlertService(db).sync_all_checks()
        assert _active(db, f"check:{check.id}") is None

    def test_rejected_events_are_not_resolved_by_the_sweep_and_get_archived_later(self, db, sales_rep):
        client = _make_client(db)
        check = _received_check(db, sales_rep, client, payment_in=-5, due_in=1)
        CheckService(db).reject(check.id, CheckRejectRequest())
        service = NotificationAlertService(db)

        service.sync_all_checks()
        rejected = _active(db, f"check_rejected:{check.id}")
        assert rejected is not None

        from datetime import datetime, timezone
        rejected.notified_at = datetime.now(timezone.utc) - timedelta(days=45)
        db.flush()
        result = service.archive_and_purge()
        assert result["archived"] == 1
        assert _active(db, f"check_rejected:{check.id}") is None


# ----------------------------------------------------------------------
# Lectura por usuario
# ----------------------------------------------------------------------

class TestReadState:
    def test_read_state_is_per_user(self, db, sales_rep, superuser):
        product = _make_product(db, stock=0, stock_min=5)
        NotificationAlertService(db).sync_product_stock(product)
        notification = _active(db, f"stock:{product.id}")
        service = NotificationService(db)

        service.mark_read(notification.id, sales_rep.id)

        assert service.get_unread_count(sales_rep.id)["unread_count"] == 0
        assert service.get_unread_count(superuser.id)["unread_count"] == 1

    def test_mark_read_is_idempotent(self, db, sales_rep):
        product = _make_product(db, stock=0, stock_min=5)
        NotificationAlertService(db).sync_product_stock(product)
        notification = _active(db, f"stock:{product.id}")
        service = NotificationService(db)
        service.mark_read(notification.id, sales_rep.id)
        service.mark_read(notification.id, sales_rep.id)
        assert service.get_unread_count(sales_rep.id)["unread_count"] == 0

    def test_mark_all_read_by_category(self, db, sales_rep):
        product = _make_product(db, stock=0, stock_min=5)
        client = _make_client(db)
        NotificationAlertService(db).sync_product_stock(product)
        _received_check(db, sales_rep, client, payment_in=-5, due_in=-1)
        service = NotificationService(db)
        assert service.get_unread_count(sales_rep.id)["by_category"] == {"stock": 1, "check": 1}

        result = service.mark_all_read(sales_rep.id, "stock")
        assert result["marked"] == 1
        assert result["unread_count"] == 1
        assert service.get_unread_count(sales_rep.id)["by_category"] == {"check": 1}

    def test_resolved_notifications_are_hidden_unless_requested(self, db, sales_rep):
        product = _make_product(db, stock=0, stock_min=5)
        service = NotificationAlertService(db)
        service.sync_product_stock(product)
        product.stock_current = 100
        service.sync_product_stock(product)

        listing = NotificationService(db)
        assert listing.get_notifications(sales_rep.id)["total"] == 0
        history = listing.get_notifications(sales_rep.id, include_resolved=True)
        assert history["total"] == 1
        assert history["items"][0]["resolved_at"] is not None


# ----------------------------------------------------------------------
# API
# ----------------------------------------------------------------------

class TestNotificationsApi:
    def test_requires_authentication(self, client):
        assert client.get("/api/notifications").status_code == 401
        assert client.get("/api/notifications/unread-count").status_code == 401
        assert client.post("/api/notifications/read-all").status_code == 401

    def test_list_count_read_and_read_all(self, client, db, auth_headers, super_headers):
        product = _make_product(db, stock=0, stock_min=5, name="Pilas AA x4")
        NotificationAlertService(db).sync_product_stock(product)

        listing = client.get("/api/notifications", headers=auth_headers)
        assert listing.status_code == 200
        body = listing.json()
        assert body["total"] == 1 and body["unread_count"] == 1
        item = body["items"][0]
        assert item["type"] == "stock_out"
        assert item["category"] == "stock"
        assert item["entity_type"] == "product" and item["entity_id"] == product.id
        assert item["is_read"] is False
        assert "Pilas AA x4" in item["title"]

        count = client.get("/api/notifications/unread-count", headers=auth_headers).json()
        assert count == {"unread_count": 1, "by_category": {"stock": 1}}

        read = client.post(f"/api/notifications/{item['id']}/read", headers=auth_headers)
        assert read.status_code == 200
        assert read.json() == {"id": item["id"], "is_read": True}

        assert client.get("/api/notifications/unread-count", headers=auth_headers).json()["unread_count"] == 0
        assert client.get("/api/notifications?unread_only=true", headers=auth_headers).json()["total"] == 0
        # Otro usuario sigue sin leerla
        assert client.get("/api/notifications/unread-count", headers=super_headers).json()["unread_count"] == 1

        done = client.post("/api/notifications/read-all", headers=super_headers)
        assert done.status_code == 200
        assert done.json() == {"marked": 1, "unread_count": 0}

    def test_filters_and_validation(self, client, db, auth_headers, sales_rep):
        product = _make_product(db, stock=0, stock_min=5)
        supplier = _make_supplier(db)
        NotificationAlertService(db).sync_product_stock(product)
        _issued_check(db, sales_rep, supplier, payment_in=0, due_in=30)

        assert client.get("/api/notifications?category=stock", headers=auth_headers).json()["total"] == 1
        assert client.get("/api/notifications?category=check", headers=auth_headers).json()["total"] == 1
        assert client.get("/api/notifications?type=check_payable", headers=auth_headers).json()["total"] == 1
        assert client.get("/api/notifications?category=otra", headers=auth_headers).status_code == 400
        assert client.get("/api/notifications?type=inventada", headers=auth_headers).status_code == 400

    def test_mark_read_unknown_notification_is_404(self, client, auth_headers):
        assert client.post("/api/notifications/999999/read", headers=auth_headers).status_code == 404
