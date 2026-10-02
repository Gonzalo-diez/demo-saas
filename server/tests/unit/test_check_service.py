"""
test_check_service.py — Tests de integración (BD sqlite real) para el
ciclo de vida de cheques: se registran 'pendientes' sin tocar el saldo de
cuenta corriente, y recién al acreditarlos se genera el
cobro/pago real (con sus imputaciones). Si se rechazan, no hay nada que
revertir porque el saldo nunca se tocó.
"""
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.core.security import get_password_hash
from app.models.client_model import Client
from app.models.supplier_model import Supplier


def _make_client(db, name="Cliente Cheques"):
    client = Client(
        name=name,
        client_type="B2B",
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
    )
    db.add(client)
    db.flush()
    return client


def _make_supplier(db, name="Proveedor Cheques"):
    supplier = Supplier(name=name, is_active=True)
    db.add(supplier)
    db.flush()
    return supplier


def _make_sales_invoice(db, sales_rep, client, *, total=Decimal("1000.00"), invoice_number=None):
    from app.services.sales_invoice_service import SalesInvoiceService
    from app.schemas.sales_invoice_schema import SalesInvoiceCreate, SalesInvoiceItemCreate
    from app.models.product_model import Product
    from app.utils.slug import slugify
    import uuid

    unique = uuid.uuid4().hex[:8]
    invoice_number = invoice_number or f"V-CHK-{unique}"

    product = Product(
        name=f"Producto Cheques {unique}",
        name_normalized=f"producto cheques {unique}",
        brand="Marca",
        brand_normalized="marca",
        category="pilas",
        category_normalized="pilas",
        slug=slugify("Producto Cheques") + f"-{unique}",
        unit_price=total,
        unit_cost=Decimal("500.00"),
        stock_current=100,
        sku=f"SKU-CHK-{unique}",
        is_active=True,
        status="ACTIVE",
    )
    db.add(product)
    db.flush()

    svc = SalesInvoiceService(db)
    invoice = svc.create(
        SalesInvoiceCreate(
            client_id=client.id,
            sales_type="B2B",
            invoice_number=invoice_number,
            invoice_date="2026-04-01",
            items=[
                SalesInvoiceItemCreate(
                    product_id=product.id,
                    product_name=product.name,
                    quantity=1,
                )
            ],
        ),
        sales_rep,
    )
    db.flush()
    svc.update_status(invoice.id, "confirmed", sales_rep)
    db.flush()
    return invoice


class TestCheckDoesNotAffectBalanceUntilCredited:
    def test_received_check_is_pending_and_balance_untouched(self, db, sales_rep):
        from app.services.check_service import CheckService
        from app.schemas.check_schema import ReceivedCheckCreate

        client = _make_client(db)
        invoice = _make_sales_invoice(db, sales_rep, client, total=Decimal("1000.00"))
        db.refresh(client)
        balance_before = Decimal(client.current_balance)

        svc = CheckService(db)
        check = svc.register_received(
            client.id,
            ReceivedCheckCreate(
                check_number="0001234",
                bank_name="Banco Nación",
                drawer_name=client.name,
                amount=Decimal("1000.00"),
                issue_date="2026-04-01",
                payment_date="2026-04-15",
                due_date="2026-05-15",
                allocations=[{"invoice_id": invoice.id, "amount": Decimal("1000.00"), "document_type": "sales_invoice"}],
            ),
            sales_rep,
        )
        db.flush()

        assert check.status == "pendiente"
        assert check.client_account_movement_id is None

        db.refresh(client)
        db.refresh(invoice)
        # El saldo y el remito no se tocaron todavía.
        assert Decimal(client.current_balance) == balance_before
        assert invoice.payment_status == "pending"
        assert Decimal(invoice.paid_amount) == Decimal("0.00")

    def test_credit_applies_payment_and_allocation(self, db, sales_rep):
        from app.services.check_service import CheckService
        from app.schemas.check_schema import ReceivedCheckCreate

        client = _make_client(db)
        invoice = _make_sales_invoice(db, sales_rep, client, total=Decimal("1000.00"))

        svc = CheckService(db)
        check = svc.register_received(
            client.id,
            ReceivedCheckCreate(
                check_number="0001235",
                amount=Decimal("1000.00"),
                issue_date="2026-04-01",
                payment_date="2026-04-15",
                due_date="2026-05-15",
                allocations=[{"invoice_id": invoice.id, "amount": Decimal("1000.00"), "document_type": "sales_invoice"}],
            ),
            sales_rep,
        )
        db.flush()

        balance_before_credit = Decimal(client.current_balance)

        credited = svc.credit(check.id, sales_rep)
        db.flush()
        db.refresh(client)
        db.refresh(invoice)

        assert credited.status == "acreditado"
        assert credited.client_account_movement_id is not None
        assert Decimal(client.current_balance) == balance_before_credit - Decimal("1000.00")
        assert invoice.payment_status == "paid"
        assert Decimal(invoice.paid_amount) == Decimal("1000.00")

    def test_rejected_check_leaves_balance_untouched(self, db, sales_rep):
        from app.services.check_service import CheckService
        from app.schemas.check_schema import ReceivedCheckCreate, CheckRejectRequest

        client = _make_client(db)
        db.refresh(client)
        balance_before = Decimal(client.current_balance)

        svc = CheckService(db)
        check = svc.register_received(
            client.id,
            ReceivedCheckCreate(
                check_number="0001236",
                amount=Decimal("500.00"),
                issue_date="2026-04-01",
                payment_date="2026-04-15",
                due_date="2026-05-15",
            ),
            sales_rep,
        )
        db.flush()

        rejected = svc.reject(check.id, CheckRejectRequest(notes="Rebotó por fondos"))
        db.flush()
        db.refresh(client)

        assert rejected.status == "rechazado"
        assert Decimal(client.current_balance) == balance_before

        # Un cheque ya rechazado no se puede volver a acreditar.
        with pytest.raises(HTTPException):
            svc.credit(check.id, sales_rep)

    def test_issued_check_credit_reduces_supplier_debt(self, db, sales_rep):
        from app.services.check_service import CheckService
        from app.schemas.check_schema import IssuedCheckCreate
        from app.services.supplier_account_movement_service import SupplierAccountMovementService

        supplier = _make_supplier(db)
        # Generamos deuda con el proveedor para tener saldo que reducir.
        SupplierAccountMovementService(db).apply_movement(
            supplier_id=supplier.id,
            movement_type="invoice",
            amount=Decimal("2000.00"),
            reference_type="purchase_invoice",
            created_by=sales_rep.id,
        )
        db.flush()
        db.refresh(supplier)
        balance_before = Decimal(supplier.current_balance)

        svc = CheckService(db)
        check = svc.register_issued(
            supplier.id,
            IssuedCheckCreate(
                check_number="0009999",
                amount=Decimal("2000.00"),
                issue_date="2026-04-01",
                payment_date="2026-04-20",
                due_date="2026-05-20",
            ),
            sales_rep,
        )
        db.flush()
        db.refresh(supplier)
        # Pendiente: la deuda con el proveedor sigue igual.
        assert Decimal(supplier.current_balance) == balance_before

        svc.credit(check.id, sales_rep)
        db.flush()
        db.refresh(supplier)
        assert Decimal(supplier.current_balance) == balance_before - Decimal("2000.00")


class TestDirectPaymentBlocksCheque:
    def test_register_payment_rejects_cheque_method(self, db, sales_rep):
        from app.services.client_account_movement_service import ClientAccountMovementService
        from app.schemas.account_movement_schema import ClientPaymentCreate

        client = _make_client(db)
        svc = ClientAccountMovementService(db)

        with pytest.raises(HTTPException) as exc_info:
            svc.register_payment(
                client.id,
                ClientPaymentCreate(amount=Decimal("100.00"), payment_method="cheque"),
                sales_rep,
            )
        assert exc_info.value.status_code == 400


class TestPendingChecksVisibility:
    def test_pending_summary_for_client(self, db, sales_rep):
        from app.services.check_service import CheckService
        from app.schemas.check_schema import ReceivedCheckCreate

        client = _make_client(db)
        svc = CheckService(db)

        svc.register_received(
            client.id,
            ReceivedCheckCreate(
                check_number="0002001",
                amount=Decimal("300.00"),
                issue_date="2026-05-01",
                payment_date="2026-05-10",
                due_date="2026-06-10",
            ),
            sales_rep,
        )
        db.flush()

        summary = svc.get_pending_summary_for_client(client.id)
        assert summary["pending_count"] == 1
        assert summary["pending_amount"] == Decimal("300.00")

        # Al acreditarlo, deja de contar como pendiente.
        checks = summary["checks"]
        svc.credit(checks[0].id, sales_rep)
        db.flush()

        summary_after = svc.get_pending_summary_for_client(client.id)
        assert summary_after["pending_count"] == 0
        assert summary_after["pending_amount"] == Decimal("0")

    def test_pending_checks_for_document(self, db, sales_rep):
        from app.services.check_service import CheckService
        from app.schemas.check_schema import ReceivedCheckCreate

        client = _make_client(db)
        invoice = _make_sales_invoice(db, sales_rep, client, total=Decimal("1000.00"))

        svc = CheckService(db)
        svc.register_received(
            client.id,
            ReceivedCheckCreate(
                check_number="0002002",
                amount=Decimal("1000.00"),
                issue_date="2026-05-01",
                payment_date="2026-05-10",
                due_date="2026-06-10",
                allocations=[{"invoice_id": invoice.id, "amount": Decimal("1000.00"), "document_type": "sales_invoice"}],
            ),
            sales_rep,
        )
        db.flush()

        result = svc.get_pending_checks_for_document("sales_invoice", invoice.id)
        assert result["pending_amount"] == Decimal("1000.00")
        assert len(result["checks"]) == 1

        # Un remito sin cheque asociado no muestra nada pendiente.
        other_invoice = _make_sales_invoice(db, sales_rep, client, total=Decimal("50.00"))
        empty_result = svc.get_pending_checks_for_document("sales_invoice", other_invoice.id)
        assert empty_result["pending_amount"] == Decimal("0")
        assert empty_result["checks"] == []