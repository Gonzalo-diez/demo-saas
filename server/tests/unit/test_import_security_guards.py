"""
test_import_security_guards.py — Tests de integración (BD sqlite real, vía
fixture `db` de conftest) para las medidas de seguridad agregadas a
import/creación de productos, remitos y presupuestos:

1) Resolución de producto por SKU o nombre + costo promedio ponderado al
   confirmar una compra.
2) Rechazo de remitos/presupuestos duplicados (mismo proveedor/cliente +
   misma fecha + mismos productos/cantidades).
"""
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.product_model import Product
from app.models.supplier_model import Supplier
from app.models.client_model import Client
from app.utils.slug import slugify
from app.core.security import get_password_hash


def _make_product(db, *, name="Aceite 1L", sku="SKU-1", stock=10, unit_cost="100.00"):
    product = Product(
        name=name,
        name_normalized=name.strip().lower(),
        brand="Marca",
        brand_normalized="marca",
        category="pilas",
        category_normalized="pilas",
        slug=slugify(name) + "-" + sku.lower(),
        unit_price=Decimal("150.00"),
        unit_cost=Decimal(unit_cost),
        stock_current=stock,
        sku=sku,
        is_active=True,
        status="ACTIVE",
    )
    db.add(product)
    db.flush()
    return product


def _make_supplier(db, name="Proveedor Test"):
    supplier = Supplier(name=name, is_active=True)
    db.add(supplier)
    db.flush()
    return supplier


def _make_client(db, name="Cliente Test"):
    client = Client(
        name=name,
        client_type="B2B",
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
    )
    db.add(client)
    db.flush()
    return client


class TestProductResolutionAndWeightedCost:
    def test_find_by_sku_or_name_falls_back_to_name(self, db):
        from app.repositories.product_repository import ProductRepository

        _make_product(db, name="Detergente Ala", sku="SKU-77")
        repo = ProductRepository(db)

        # Sin SKU (o con uno que no matchea), debe encontrarlo por nombre.
        found = repo.find_by_sku_or_name(None, "Detergente Ala")
        assert found is not None
        assert found.sku == "SKU-77"

        found_by_wrong_sku = repo.find_by_sku_or_name("NO-EXISTE", "Detergente Ala")
        assert found_by_wrong_sku is not None
        assert found_by_wrong_sku.sku == "SKU-77"

    def test_purchase_invoice_confirm_applies_weighted_cost_matching_by_name(self, db, sales_rep):
        from app.services.purchase_invoice_service import PurchaseInvoiceService
        from app.schemas.purchase_invoice_schema import (
            PurchaseInvoiceCreate,
            PurchaseInvoiceItemCreate,
        )

        product = _make_product(db, name="Lavandina 1L", sku="SKU-100", stock=10, unit_cost="100.00")
        supplier = _make_supplier(db)
        svc = PurchaseInvoiceService(db)

        # El item viene SIN product_id (como en un import de PDF): debe
        # vincularse al producto existente por nombre al confirmar, y
        # ponderar el costo: (10*100 + 10*200) / 20 = 150.
        invoice = svc.create(
            PurchaseInvoiceCreate(
                supplier_id=supplier.id,
                supplier_name=supplier.name,
                invoice_number="F-0001",
                invoice_date="2026-01-10",
                items=[
                    PurchaseInvoiceItemCreate(
                        product_name="Lavandina 1L",
                        quantity=10,
                        unit_cost=Decimal("200.00"),
                    )
                ],
            ),
            sales_rep,
        )
        db.flush()

        svc.update_status(invoice.id, "confirmed", sales_rep)
        db.flush()
        db.refresh(product)

        assert product.stock_current == 20
        assert product.unit_cost == Decimal("150.00")


class TestDuplicateGuards:
    def test_duplicate_purchase_invoice_is_rejected(self, db, sales_rep):
        from app.services.purchase_invoice_service import PurchaseInvoiceService
        from app.schemas.purchase_invoice_schema import (
            PurchaseInvoiceCreate,
            PurchaseInvoiceItemCreate,
        )

        supplier = _make_supplier(db)
        svc = PurchaseInvoiceService(db)

        payload = PurchaseInvoiceCreate(
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            invoice_number="F-0001",
            invoice_date="2026-02-01",
            items=[
                PurchaseInvoiceItemCreate(
                    product_name="Producto X",
                    quantity=5,
                    unit_cost=Decimal("50.00"),
                )
            ],
        )
        svc.create(payload, sales_rep)
        db.flush()

        # Mismo proveedor, misma fecha, mismos productos/cantidades, pero
        # otro número de remito (como si se hubiese reimportado el mismo
        # PDF con un invoice_number generado distinto).
        dup_payload = payload.model_copy(update={"invoice_number": "F-0002"})

        with pytest.raises(HTTPException) as exc_info:
            svc.create(dup_payload, sales_rep)
        assert exc_info.value.status_code == 409

        # Con force=True, se permite crearlo igual.
        forced_payload = payload.model_copy(update={"invoice_number": "F-0003", "force": True})
        forced = svc.create(forced_payload, sales_rep)
        assert forced.id is not None

    def test_duplicate_sales_invoice_is_rejected(self, db, sales_rep):
        from app.services.sales_invoice_service import SalesInvoiceService
        from app.schemas.sales_invoice_schema import (
            SalesInvoiceCreate,
            SalesInvoiceItemCreate,
        )

        client = _make_client(db)
        product = _make_product(db, name="Jabón en polvo", sku="SKU-200", stock=100)
        svc = SalesInvoiceService(db)

        payload = SalesInvoiceCreate(
            client_id=client.id,
            sales_type="B2B",
            invoice_number="V-0001",
            invoice_date="2026-02-05",
            items=[
                SalesInvoiceItemCreate(
                    product_id=product.id,
                    product_name=product.name,
                    quantity=2,
                )
            ],
        )
        svc.create(payload, sales_rep)
        db.flush()

        dup_payload = payload.model_copy(update={"invoice_number": "V-0002"})
        with pytest.raises(HTTPException) as exc_info:
            svc.create(dup_payload, sales_rep)
        assert exc_info.value.status_code == 409

    def test_different_quantity_is_not_flagged_as_duplicate(self, db, sales_rep):
        """Un remito con distinta cantidad para el mismo proveedor/fecha
        no debe rechazarse: no es el mismo documento."""
        from app.services.purchase_invoice_service import PurchaseInvoiceService
        from app.schemas.purchase_invoice_schema import (
            PurchaseInvoiceCreate,
            PurchaseInvoiceItemCreate,
        )

        supplier = _make_supplier(db)
        svc = PurchaseInvoiceService(db)

        base_items = dict(product_name="Producto Y", unit_cost=Decimal("10.00"))

        svc.create(
            PurchaseInvoiceCreate(
                supplier_id=supplier.id,
                supplier_name=supplier.name,
                invoice_number="F-1001",
                invoice_date="2026-03-01",
                items=[PurchaseInvoiceItemCreate(quantity=5, **base_items)],
            ),
            sales_rep,
        )
        db.flush()

        # Misma fecha/proveedor/producto, pero otra cantidad -> no duplicado.
        second = svc.create(
            PurchaseInvoiceCreate(
                supplier_id=supplier.id,
                supplier_name=supplier.name,
                invoice_number="F-1002",
                invoice_date="2026-03-01",
                items=[PurchaseInvoiceItemCreate(quantity=7, **base_items)],
            ),
            sales_rep,
        )
        assert second.id is not None
