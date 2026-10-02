"""
Repara Client.current_balance para remitos de venta que quedaron
"confirmed" sin registrar el movimiento de deuda correspondiente.

Contexto
--------
Hasta este fix, cuando una orden (B2B u ONLINE) pasaba a "preparing" y
tenía un `customer_email`, el remito (SalesInvoice) se marcaba
directamente como `status = "confirmed"` sin pasar por
`SalesInvoiceService.update_status`. Eso significa que nunca se llamó a
`_register_invoice_receivable`, así que el remito quedó confirmado (y
aparece en la antigüedad de deuda, que lee directo de SalesInvoice) pero
**nunca se creó el movimiento de cuenta corriente** correspondiente ni
se actualizó `current_balance` — por eso el saldo se veía siempre en
$0,00.

Este script busca esos remitos "huérfanos" (confirmed, con cliente
asociado, sin su movimiento de tipo 'invoice') y crea el movimiento
faltante, lo que además actualiza el `current_balance` correspondiente.

Uso
---
    # Solo mostrar qué se repararía, sin tocar la base:
    python -m app.scripts.repair_client_invoice_movements

    # Aplicar la reparación de verdad:
    python -m app.scripts.repair_client_invoice_movements --apply
"""

import argparse

from sqlalchemy import select

from app.db.base import SessionLocal

# Importar todos los modelos para que SQLAlchemy pueda resolver las
# relaciones (p. ej. Client -> AnalyticsClientDaily) cuando el script
# corre con su propia sesión, sin pasar por main.py que normalmente
# registra todo. Mismo patrón que usan los jobs de analytics
# (app/analytics/jobs/base_job.py).
import app.models  # noqa: F401
import app.analytics.models.analytics_product_daily_model  # noqa: F401
import app.analytics.models.analytics_daily_model  # noqa: F401
import app.analytics.models.analytics_sales_rep_daily_model  # noqa: F401
import app.analytics.models.analytics_client_daily_model  # noqa: F401
import app.analytics.models.analytics_zone_product_daily_model  # noqa: F401
import app.analytics.models.analytics_catalog_event_model  # noqa: F401

from app.models.client_account_movement_model import ClientAccountMovement
from app.models.sales_invoice_model import SalesInvoice
from app.services.client_account_movement_service import ClientAccountMovementService


def find_missing_client_invoice_movements(db) -> list[SalesInvoice]:
    """
    Remitos confirmados, con cliente asociado y monto > 0, para los que
    no existe todavía un ClientAccountMovement de tipo 'invoice'.
    """
    existing_reference_ids = set(
        db.scalars(
            select(ClientAccountMovement.reference_id).where(
                ClientAccountMovement.reference_type == "sales_invoice",
                ClientAccountMovement.movement_type == "invoice",
                ClientAccountMovement.reference_id.is_not(None),
            )
        ).all()
    )

    invoices = db.scalars(
        select(SalesInvoice).where(
            SalesInvoice.status == "confirmed",
            SalesInvoice.client_id.is_not(None),
        )
    ).all()

    return [
        invoice
        for invoice in invoices
        if invoice.id not in existing_reference_ids
        and invoice.total_amount
        and invoice.total_amount > 0
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica los cambios. Sin este flag solo hace un dry-run.",
    )
    args = parser.parse_args()

    db = SessionLocal()

    try:
        missing_clients = find_missing_client_invoice_movements(db)

        if not missing_clients:
            print("No hay remitos con movimientos faltantes. Todo en orden.")
            return

        client_service = ClientAccountMovementService(db)

        print(f"Remitos de clientes con movimiento faltante: {len(missing_clients)}\n")

        for invoice in missing_clients:
            print(
                f"  - Remito #{invoice.id} ({invoice.invoice_number}) | "
                f"cliente_id={invoice.client_id} | monto=${invoice.total_amount}"
            )

            if args.apply:
                client_service.apply_movement(
                    client_id=invoice.client_id,
                    movement_type="invoice",
                    amount=invoice.total_amount,
                    reference_type="sales_invoice",
                    reference_id=invoice.id,
                    notes=(
                        f"Reparación automática — remito de venta #{invoice.id} "
                        "confirmado sin movimiento de cuenta corriente"
                    ),
                )

        total = len(missing_clients)

        if args.apply:
            db.commit()
            print(f"\nListo. Se repararon {total} remito(s).")
        else:
            print(
                "\nEsto fue un dry-run, no se modificó nada. "
                "Volvé a correr con --apply para aplicar los cambios."
            )

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
