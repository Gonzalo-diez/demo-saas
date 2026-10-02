from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.sales_invoice_model import SalesInvoice


def _serialize_invoice(inv: SalesInvoice) -> dict:
    return {
        "id": inv.id,
        "invoice_number": inv.invoice_number,
        "invoice_date": inv.invoice_date.isoformat() if inv.invoice_date else None,
        "status": inv.status,
        "sales_type": inv.sales_type,
        "client_id": inv.client_id,
        "client_name": inv.client.name if inv.client else inv.customer_name,
        "client_branch_id": inv.client_branch_id,
        "client_branch_name": inv.client_branch.name if inv.client_branch else None,
        "sales_rep_id": inv.sales_rep_id,
        "sales_rep_name": inv.sales_rep.name if inv.sales_rep else None,
        "total_cost": float(inv.total_cost) if inv.total_cost is not None else None,
        "total_amount": float(inv.total_amount) if inv.total_amount is not None else None,
        "margin_amount": float(inv.margin_amount) if inv.margin_amount is not None else None,
        "currency": inv.currency,
        "items_count": len(inv.items) if inv.items else 0,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
    }


def get_recent_sales_invoices_tool(db: Session, limit: int = 10) -> dict:
    stmt = (
        select(SalesInvoice)
        .options(
            joinedload(SalesInvoice.client),
            joinedload(SalesInvoice.client_branch),
            joinedload(SalesInvoice.sales_rep),
            selectinload(SalesInvoice.items),
        )
        .order_by(SalesInvoice.invoice_date.desc(), SalesInvoice.created_at.desc())
        .limit(limit)
    )

    invoices = list(db.scalars(stmt).unique().all())

    return {
        "count": len(invoices),
        "items": [_serialize_invoice(i) for i in invoices],
    }


def get_sales_invoice_overview_tool(db: Session) -> dict:
    total = db.scalar(select(func.count()).select_from(SalesInvoice)) or 0
    total_amount = db.scalar(
        select(func.sum(SalesInvoice.total_amount)).where(
            SalesInvoice.status != "cancelled"
        )
    ) or 0
    total_cost = db.scalar(
        select(func.sum(SalesInvoice.total_cost)).where(
            SalesInvoice.status != "cancelled"
        )
    ) or 0
    total_margin = db.scalar(
        select(func.sum(SalesInvoice.margin_amount)).where(
            SalesInvoice.status != "cancelled"
        )
    ) or 0

    by_status_stmt = (
        select(SalesInvoice.status, func.count(SalesInvoice.id))
        .group_by(SalesInvoice.status)
        .order_by(func.count(SalesInvoice.id).desc())
    )
    by_status = [
        {"status": status, "count": count}
        for status, count in db.execute(by_status_stmt).all()
    ]

    by_sales_type_stmt = (
        select(SalesInvoice.sales_type, func.count(SalesInvoice.id))
        .group_by(SalesInvoice.sales_type)
        .order_by(func.count(SalesInvoice.id).desc())
    )
    by_sales_type = [
        {"sales_type": st, "count": count}
        for st, count in db.execute(by_sales_type_stmt).all()
    ]

    return {
        "total_invoices": total,
        "total_amount": float(total_amount),
        "total_cost": float(total_cost),
        "total_margin": float(total_margin),
        "by_status": by_status,
        "by_sales_type": by_sales_type,
    }