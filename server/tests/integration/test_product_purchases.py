"""
Historial de compras por producto, vencimiento y precio de venta por % de remarque.
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.utils.pricing import price_from_markup, round_sale_price

from tests.integration.test_product_categories import _category, _product
from tests.integration.test_tenant_isolation import (  # noqa: F401
    _bearer,
    rep_a,
    rep_b,
    tenant_b,
)


def _create(client, headers, sku, **extra):
    """Alta de producto por la API, con los datos mínimos (sin precio fijo salvo que se pase)."""
    cat = _category(client, headers, f"Cat {sku}")
    payload = {
        "name": f"Prod {sku}",
        "brand": "Marca",
        "category_id": cat["id"],
        "unit_cost": "200.00",
        "sku": sku,
        "stock_current": 0,
        "image_url": "https://example.com/i.jpg",
    }
    payload.update(extra)
    return client.post("/api/products/", json=payload, headers=headers)


def _purchases(client, headers, product_id, **params):
    resp = client.get(f"/api/products/{product_id}/purchases/", params=params, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ═══════════════════════════════════════════════════════════════════════════
# Cálculo del precio
# ═══════════════════════════════════════════════════════════════════════════

class TestPricing:
    def test_markup_example_200_plus_40_is_280(self):
        assert price_from_markup(Decimal("200"), Decimal("40")) == Decimal("280.00")

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("400.50", "401.00"),   # la mitad sube
            ("400.49", "400.00"),
            ("400.51", "401.00"),
            ("400.00", "400.00"),
            ("0.49", "0.00"),
            ("0.50", "1.00"),
        ],
    )
    def test_rounds_to_whole_pesos(self, value, expected):
        assert round_sale_price(Decimal(value)) == Decimal(expected)

    def test_markup_result_is_rounded(self):
        # 286,07 + 40% = 400,498 -> 400 · 286,10 + 40% = 400,54 -> 401
        assert price_from_markup(Decimal("286.07"), Decimal("40")) == Decimal("400.00")
        assert price_from_markup(Decimal("286.10"), Decimal("40")) == Decimal("401.00")
        # 250,36 + 60% = 400,576 -> 401
        assert price_from_markup(Decimal("250.36"), Decimal("60")) == Decimal("401.00")

    def test_zero_markup_and_zero_cost(self):
        assert price_from_markup(Decimal("123.40"), Decimal("0")) == Decimal("123.00")
        assert price_from_markup(Decimal("0"), Decimal("50")) == Decimal("0.00")


# ═══════════════════════════════════════════════════════════════════════════
# Alta de producto con remarque y vencimiento
# ═══════════════════════════════════════════════════════════════════════════

class TestCreateProductWithMarkup:
    def test_price_is_computed_from_cost_and_markup(self, client, auth_headers):
        resp = _create(client, auth_headers, "m1", unit_cost="200.00", markup_percent="40")
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert Decimal(body["unit_price"]) == Decimal("280.00")
        assert Decimal(body["markup_percent"]) == Decimal("40.00")

    def test_computed_price_is_rounded(self, client, auth_headers):
        resp = _create(client, auth_headers, "m2", unit_cost="286.10", markup_percent="40")
        assert resp.status_code == 201
        assert Decimal(resp.json()["unit_price"]) == Decimal("401.00")

    def test_explicit_price_still_works_without_markup(self, client, auth_headers):
        resp = _create(client, auth_headers, "m3", unit_price="350.50")
        assert resp.status_code == 201
        assert Decimal(resp.json()["unit_price"]) == Decimal("350.50")
        assert resp.json()["markup_percent"] is None

    def test_markup_wins_over_price_when_both_are_sent(self, client, auth_headers):
        resp = _create(client, auth_headers, "m4", unit_price="999", markup_percent="50")
        assert resp.status_code == 201
        assert Decimal(resp.json()["unit_price"]) == Decimal("300.00")

    def test_needs_price_or_markup(self, client, auth_headers):
        resp = _create(client, auth_headers, "m5")
        assert resp.status_code == 422

    def test_markup_cannot_be_negative(self, client, auth_headers):
        assert _create(client, auth_headers, "m6", markup_percent="-5").status_code == 422

    def test_update_with_markup_recalculates_price(self, client, auth_headers):
        pid = _create(client, auth_headers, "m7", markup_percent="40").json()["id"]
        resp = client.patch(
            f"/api/products/{pid}",
            json={"unit_cost": "300.00", "markup_percent": "30"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        assert Decimal(resp.json()["unit_price"]) == Decimal("390.00")
        assert Decimal(resp.json()["markup_percent"]) == Decimal("30.00")

    def test_resending_the_same_price_keeps_saved_markup(self, client, auth_headers):
        # El formulario de edición reenvía el precio aunque solo cambies el nombre.
        created = _create(client, auth_headers, "m7b", unit_cost="200.00", markup_percent="40").json()
        resp = client.patch(
            f"/api/products/{created['id']}",
            json={"name": "Otro nombre", "unit_price": "280.00", "unit_cost": "200.00"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        assert Decimal(resp.json()["unit_price"]) == Decimal("280.00")
        assert Decimal(resp.json()["markup_percent"]) == Decimal("40.00")

    def test_manual_price_on_update_clears_saved_markup(self, client, auth_headers):
        pid = _create(client, auth_headers, "m8", markup_percent="40").json()["id"]
        resp = client.patch(f"/api/products/{pid}", json={"unit_price": "333.00"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["markup_percent"] is None


class TestInitialStockCreatesHistory:
    def test_initial_stock_is_the_first_purchase_with_expiry(self, client, auth_headers):
        expiry = (date.today() + timedelta(days=90)).isoformat()
        resp = _create(
            client, auth_headers, "h1",
            stock_current=50, markup_percent="40", expiry_date=expiry,
        )
        assert resp.status_code == 201, resp.text
        pid = resp.json()["id"]

        history = _purchases(client, auth_headers, pid)
        assert history["total"] == 1
        first = history["items"][0]
        assert first["source"] == "initial_stock"
        assert first["quantity"] == 50
        assert Decimal(first["unit_cost"]) == Decimal("200.00")
        assert Decimal(first["sale_price"]) == Decimal("280.00")
        assert Decimal(first["markup_percent"]) == Decimal("40.00")
        assert first["expiry_date"] == expiry
        assert first["created_by_name"]

    def test_no_stock_means_no_history(self, client, auth_headers):
        pid = _create(client, auth_headers, "h2", markup_percent="40").json()["id"]
        assert _purchases(client, auth_headers, pid)["total"] == 0

    def test_expiry_without_stock_is_rejected(self, client, auth_headers):
        expiry = (date.today() + timedelta(days=30)).isoformat()
        resp = _create(client, auth_headers, "h3", markup_percent="40", expiry_date=expiry)
        assert resp.status_code == 400
        assert "stock" in resp.json()["detail"].lower()

    def test_past_expiry_is_rejected(self, client, auth_headers):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        resp = _create(
            client, auth_headers, "h4", stock_current=5, markup_percent="40", expiry_date=yesterday
        )
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════════════════
# Compras sucesivas: x cantidad a y costo, después z cantidad a l costo
# ═══════════════════════════════════════════════════════════════════════════

class TestRegisterPurchases:
    def test_two_purchases_at_different_costs_are_both_recorded(self, client, auth_headers):
        pid = _create(client, auth_headers, "p1", stock_current=10, unit_cost="100.00", markup_percent="50").json()["id"]

        first = client.post(
            f"/api/products/{pid}/purchases/",
            json={"quantity": 10, "unit_cost": "200.00", "markup_percent": "40"},
            headers=auth_headers,
        )
        assert first.status_code == 201, first.text
        assert Decimal(first.json()["sale_price"]) == Decimal("280.00")

        second = client.post(
            f"/api/products/{pid}/purchases/",
            json={"quantity": 20, "unit_cost": "250.00", "markup_percent": "40",
                  "expiry_date": (date.today() + timedelta(days=60)).isoformat()},
            headers=auth_headers,
        )
        assert second.status_code == 201, second.text
        assert Decimal(second.json()["sale_price"]) == Decimal("350.00")

        history = _purchases(client, auth_headers, pid)
        assert history["total"] == 3  # stock inicial + 2 compras
        # la más reciente primero
        assert [Decimal(i["unit_cost"]) for i in history["items"]] == [
            Decimal("250.00"), Decimal("200.00"), Decimal("100.00"),
        ]

    def test_backdated_purchase_is_listed_by_its_date(self, client, auth_headers):
        pid = _create(client, auth_headers, "p1b", stock_current=10, unit_cost="100.00", markup_percent="50").json()["id"]
        client.post(
            f"/api/products/{pid}/purchases/",
            json={"quantity": 5, "unit_cost": "90.00",
                  "purchase_date": (date.today() - timedelta(days=30)).isoformat()},
            headers=auth_headers,
        )
        items = _purchases(client, auth_headers, pid)["items"]
        # el stock inicial es de hoy; la compra cargada con fecha vieja queda abajo
        assert [i["source"] for i in items] == ["initial_stock", "manual"]
        assert items[1]["purchase_date"] == (date.today() - timedelta(days=30)).isoformat()

    def test_purchase_adds_stock_weighted_cost_and_price(self, client, auth_headers):
        pid = _create(client, auth_headers, "p2", stock_current=10, unit_cost="100.00", markup_percent="50").json()["id"]
        client.post(
            f"/api/products/{pid}/purchases/",
            json={"quantity": 30, "unit_cost": "200.00", "markup_percent": "40"},
            headers=auth_headers,
        )
        product = client.get(f"/api/products/{pid}", headers=auth_headers).json()
        assert product["stock_current"] == 40
        # costo promedio ponderado: (10*100 + 30*200) / 40 = 175
        assert Decimal(product["unit_cost"]) == Decimal("175.00")
        # el precio pasa a ser el de la última compra: 200 + 40% = 280
        assert Decimal(product["unit_price"]) == Decimal("280.00")
        assert Decimal(product["markup_percent"]) == Decimal("40.00")

    def test_purchase_can_leave_product_price_untouched(self, client, auth_headers):
        pid = _create(client, auth_headers, "p3", stock_current=5, unit_cost="100.00", unit_price="150.00").json()["id"]
        resp = client.post(
            f"/api/products/{pid}/purchases/",
            json={"quantity": 5, "unit_cost": "200.00", "markup_percent": "40",
                  "update_product_price": False},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert Decimal(resp.json()["sale_price"]) == Decimal("280.00")  # queda anotado en la compra
        assert Decimal(client.get(f"/api/products/{pid}", headers=auth_headers).json()["unit_price"]) == Decimal("150.00")

    def test_purchase_without_markup_keeps_price(self, client, auth_headers):
        pid = _create(client, auth_headers, "p4", stock_current=5, unit_cost="100.00", unit_price="150.00").json()["id"]
        resp = client.post(
            f"/api/products/{pid}/purchases/",
            json={"quantity": 5, "unit_cost": "120.00"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["sale_price"] is None
        assert Decimal(client.get(f"/api/products/{pid}", headers=auth_headers).json()["unit_price"]) == Decimal("150.00")

    def test_purchase_with_fixed_sale_price(self, client, auth_headers):
        pid = _create(client, auth_headers, "p5", stock_current=5, unit_cost="100.00", markup_percent="50").json()["id"]
        resp = client.post(
            f"/api/products/{pid}/purchases/",
            json={"quantity": 5, "unit_cost": "120.00", "sale_price": "199.00"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        product = client.get(f"/api/products/{pid}", headers=auth_headers).json()
        assert Decimal(product["unit_price"]) == Decimal("199.00")
        assert product["markup_percent"] is None  # fijado a mano: el remarque ya no aplica

    def test_markup_and_fixed_price_together_are_rejected(self, client, auth_headers):
        pid = _create(client, auth_headers, "p6", unit_price="150").json()["id"]
        resp = client.post(
            f"/api/products/{pid}/purchases/",
            json={"quantity": 5, "unit_cost": "100", "markup_percent": "40", "sale_price": "150"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    @pytest.mark.parametrize(
        "body",
        [
            {"quantity": 0, "unit_cost": "10"},
            {"quantity": -3, "unit_cost": "10"},
            {"quantity": 5, "unit_cost": "-1"},
            {"quantity": 5, "unit_cost": "10", "markup_percent": "-10"},
        ],
    )
    def test_invalid_amounts_are_rejected(self, client, auth_headers, body):
        pid = _create(client, auth_headers, "p7", unit_price="150").json()["id"]
        assert client.post(f"/api/products/{pid}/purchases/", json=body, headers=auth_headers).status_code == 422

    def test_expiry_cannot_be_before_purchase_date(self, client, auth_headers):
        pid = _create(client, auth_headers, "p8", unit_price="150").json()["id"]
        resp = client.post(
            f"/api/products/{pid}/purchases/",
            json={"quantity": 5, "unit_cost": "10",
                  "purchase_date": date.today().isoformat(),
                  "expiry_date": (date.today() - timedelta(days=2)).isoformat()},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_future_purchase_date_is_rejected(self, client, auth_headers):
        pid = _create(client, auth_headers, "p9", unit_price="150").json()["id"]
        resp = client.post(
            f"/api/products/{pid}/purchases/",
            json={"quantity": 5, "unit_cost": "10",
                  "purchase_date": (date.today() + timedelta(days=10)).isoformat()},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_unknown_product_is_404(self, client, auth_headers):
        assert client.post("/api/products/999999/purchases/",
                           json={"quantity": 1, "unit_cost": "1"}, headers=auth_headers).status_code == 404
        assert client.get("/api/products/999999/purchases/", headers=auth_headers).status_code == 404

    def test_purchase_creates_inventory_movement(self, client, auth_headers):
        pid = _create(client, auth_headers, "p10", unit_price="150").json()["id"]
        client.post(f"/api/products/{pid}/purchases/",
                    json={"quantity": 7, "unit_cost": "100"}, headers=auth_headers)
        moves = client.get("/api/inventory-movements", params={"product_id": pid}, headers=auth_headers).json()
        assert [(m["movement_type"], m["quantity"]) for m in moves["items"]] == [("purchase", 7)]


# ═══════════════════════════════════════════════════════════════════════════
# Resumen e historial
# ═══════════════════════════════════════════════════════════════════════════

class TestHistorySummary:
    def test_summary_costs_and_next_expiry(self, client, auth_headers):
        pid = _create(client, auth_headers, "s1", unit_price="500").json()["id"]
        soon = date.today() + timedelta(days=20)
        later = date.today() + timedelta(days=200)
        for qty, cost, expiry in ((10, "100.00", later), (30, "200.00", soon)):
            client.post(
                f"/api/products/{pid}/purchases/",
                json={"quantity": qty, "unit_cost": cost, "expiry_date": expiry.isoformat()},
                headers=auth_headers,
            )

        summary = _purchases(client, auth_headers, pid)["summary"]
        assert summary["purchases_count"] == 2
        assert summary["total_quantity"] == 40
        assert Decimal(summary["average_cost"]) == Decimal("175.00")  # (10*100 + 30*200) / 40
        assert Decimal(summary["last_cost"]) == Decimal("200.00")
        assert Decimal(summary["min_cost"]) == Decimal("100.00")
        assert Decimal(summary["max_cost"]) == Decimal("200.00")
        assert summary["next_expiry_date"] == soon.isoformat()

    def test_empty_history_summary(self, client, auth_headers):
        pid = _create(client, auth_headers, "s2", unit_price="500").json()["id"]
        data = _purchases(client, auth_headers, pid)
        assert data["items"] == [] and data["total"] == 0
        assert data["summary"]["purchases_count"] == 0
        assert data["summary"]["average_cost"] is None
        assert data["summary"]["next_expiry_date"] is None

    def test_pagination(self, client, auth_headers):
        pid = _create(client, auth_headers, "s3", unit_price="500").json()["id"]
        for i in range(5):
            client.post(f"/api/products/{pid}/purchases/",
                        json={"quantity": 1, "unit_cost": str(10 + i)}, headers=auth_headers)
        page1 = _purchases(client, auth_headers, pid, page=1, page_size=2)
        assert page1["total"] == 5 and len(page1["items"]) == 2
        page3 = _purchases(client, auth_headers, pid, page=3, page_size=2)
        assert len(page3["items"]) == 1

    def test_requires_login(self, client, auth_headers):
        pid = _create(client, auth_headers, "s4", unit_price="500").json()["id"]
        assert client.get(f"/api/products/{pid}/purchases/").status_code in (400, 401)
        assert client.post(f"/api/products/{pid}/purchases/",
                           json={"quantity": 1, "unit_cost": "1"}).status_code in (400, 401)


# ═══════════════════════════════════════════════════════════════════════════
# Aislamiento entre distribuidoras
# ═══════════════════════════════════════════════════════════════════════════

class TestPurchasesAreTenantScoped:
    def test_other_tenant_cannot_see_or_buy_my_product(self, client, rep_a, rep_b):
        ha, hb = _bearer(rep_a), _bearer(rep_b)
        pid = _create(client, ha, "t1", stock_current=5, markup_percent="40").json()["id"]

        assert client.get(f"/api/products/{pid}/purchases/", headers=hb).status_code == 404
        assert client.post(f"/api/products/{pid}/purchases/",
                           json={"quantity": 1, "unit_cost": "1"}, headers=hb).status_code == 404
        # y el dueño no se vio afectado
        assert _purchases(client, ha, pid)["total"] == 1

    def test_histories_do_not_mix(self, client, rep_a, rep_b):
        ha, hb = _bearer(rep_a), _bearer(rep_b)
        pa = _create(client, ha, "t2", stock_current=5, markup_percent="40").json()["id"]
        pb = _create(client, hb, "t2", stock_current=9, markup_percent="10").json()["id"]
        assert [i["quantity"] for i in _purchases(client, ha, pa)["items"]] == [5]
        assert [i["quantity"] for i in _purchases(client, hb, pb)["items"]] == [9]


# ═══════════════════════════════════════════════════════════════════════════
# Remitos de compra e importaciones también alimentan el historial
# ═══════════════════════════════════════════════════════════════════════════

class TestOtherEntryPointsFeedHistory:
    def test_confirmed_purchase_invoice_is_recorded(self, client, auth_headers):
        pid = _create(client, auth_headers, "r1", unit_price="500", unit_cost="100.00").json()["id"]
        created = client.post(
            "/api/purchase-invoices",
            json={
                "supplier_name": "Proveedor SA",
                "invoice_number": "0001-00000042",
                "invoice_date": date.today().isoformat(),
                "items": [{"product_id": pid, "product_name": "Prod r1", "quantity": 12, "unit_cost": "130.00"}],
            },
            headers=auth_headers,
        )
        assert created.status_code in (200, 201), created.text
        invoice_id = created.json()["id"]
        confirm = client.patch(
            f"/api/purchase-invoices/{invoice_id}/status",
            json={"status": "confirmed"},
            headers=auth_headers,
        )
        assert confirm.status_code == 200, confirm.text

        items = _purchases(client, auth_headers, pid)["items"]
        assert len(items) == 1
        assert items[0]["source"] == "purchase_invoice"
        assert items[0]["quantity"] == 12
        assert Decimal(items[0]["unit_cost"]) == Decimal("130.00")
        assert items[0]["reference_id"] == invoice_id

    def test_excel_import_is_recorded(self, db, tenant):
        from app.db.tenant_context import tenant_scope
        from app.schemas.product_import_schema import ProductImportRow
        from app.services.product_service import ProductService
        from app.models.product_purchase_model import ProductPurchase

        rows = [ProductImportRow(
            sku="imp-1", name="Importado", brand="Marca", category="Golosinas",
            unit_cost=Decimal("50"), unit_price=Decimal("80"), stock_current=20,
        )]
        with tenant_scope(db, tenant.id):
            ProductService(db).import_products_bulk(rows)
            # segunda importación: suma stock sobre el existente
            ProductService(db).import_products_bulk([ProductImportRow(
                sku="imp-1", name="Importado", brand="Marca", category="Golosinas",
                unit_cost=Decimal("70"), unit_price=Decimal("80"), stock_current=10,
            )])
            db.flush()
            purchases = db.query(ProductPurchase).order_by(ProductPurchase.id).all()

        assert [(p.source, p.quantity, p.unit_cost) for p in purchases] == [
            ("import", 20, Decimal("50.00")),
            ("import", 10, Decimal("70.00")),
        ]
        # El stock coincide con lo importado (antes un producto nuevo quedaba con el doble).
        from app.models.product_model import Product
        with tenant_scope(db, tenant.id):
            product = db.query(Product).filter(Product.sku == "imp-1").one()
        assert product.stock_current == 30
        assert product.unit_cost == Decimal("56.67")  # (20*50 + 10*70) / 30
