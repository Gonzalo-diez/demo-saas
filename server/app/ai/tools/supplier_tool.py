from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.supplier_model import Supplier


def _serialize_supplier(s: Supplier) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "email": s.email,
        "phone": s.phone,
        "is_active": s.is_active,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


def get_suppliers_tool(db: Session, limit: int = 20) -> dict:
    stmt = (
        select(Supplier)
        .order_by(Supplier.name.asc())
        .limit(limit)
    )

    suppliers = list(db.scalars(stmt).all())

    return {
        "count": len(suppliers),
        "items": [_serialize_supplier(s) for s in suppliers],
    }


def get_supplier_overview_tool(db: Session) -> dict:
    total = db.scalar(select(func.count()).select_from(Supplier)) or 0
    active = db.scalar(
        select(func.count()).select_from(Supplier).where(Supplier.is_active.is_(True))  # fix: select_from agregado
    ) or 0

    return {
        "total_suppliers": total,
        "active_suppliers": active,
        "inactive_suppliers": total - active,
    }