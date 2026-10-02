from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.purchase_invoice_model import PurchaseInvoice


def _serialize_purchase_invoice(inv: PurchaseInvoice) -> dict:
    return {
        "id": inv.id,
        "invoice_number": inv.invoice_number,
        "invoice_date": inv.invoice_date.isoformat() if inv.invoice_date else None,
        "status": inv.status,
        "supplier_id": inv.supplier_id,
        "supplier_name": inv.supplier_name,
        "supplier_tax_id": inv.supplier_tax_id,
        "total_amount": float(inv.total_amount) if inv.total_amount is not None else None,
        "items_count": len(inv.items) if inv.items else 0,
        "created_by_id": inv.created_by,
        "created_by_name": inv.creator.name if inv.creator else None,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
    }


def get_recent_purchase_invoices_tool(db: Session, limit: int = 10) -> dict:
    stmt = (
        select(PurchaseInvoice)
        .options(
            joinedload(PurchaseInvoice.supplier),
            joinedload(PurchaseInvoice.creator),
            selectinload(PurchaseInvoice.items),
        )
        .order_by(PurchaseInvoice.invoice_date.desc(), PurchaseInvoice.created_at.desc())
        .limit(limit)
    )

    invoices = list(db.scalars(stmt).unique().all())

    return {
        "count": len(invoices),
        "items": [_serialize_purchase_invoice(i) for i in invoices],
    }


def get_purchase_invoice_overview_tool(db: Session) -> dict:
    total = db.scalar(select(func.count()).select_from(PurchaseInvoice)) or 0
    total_amount = db.scalar(
        select(func.sum(PurchaseInvoice.total_amount)).where(
            PurchaseInvoice.status != "cancelled"
        )
    ) or 0

    by_status_stmt = (
        select(PurchaseInvoice.status, func.count(PurchaseInvoice.id))
        .group_by(PurchaseInvoice.status)
        .order_by(func.count(PurchaseInvoice.id).desc())
    )
    by_status = [
        {"status": status, "count": count}
        for status, count in db.execute(by_status_stmt).all()
    ]

    by_supplier_stmt = (
        select(PurchaseInvoice.supplier_name, func.count(PurchaseInvoice.id))
        .group_by(PurchaseInvoice.supplier_name)
        .order_by(func.count(PurchaseInvoice.id).desc())
        .limit(10)
    )
    by_supplier = [
        {"supplier_name": name, "count": count}
        for name, count in db.execute(by_supplier_stmt).all()
    ]

    return {
        "total_invoices": total,
        "total_amount": float(total_amount),
        "by_status": by_status,
        "top_suppliers_by_invoice_count": by_supplier,
    }