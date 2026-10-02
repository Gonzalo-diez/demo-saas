from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.client_model import Client
from app.models.order_model import Order
from app.models.sales_rep_model import SalesRep

def _serialize_sales_rep(rep: SalesRep) -> dict:
    return {
        "id": rep.id,
        "name": rep.name,
        "email": rep.email,
        "phone": rep.phone,
        "is_active": rep.is_active,
        "is_superuser": rep.is_superuser,
        "created_at": rep.created_at.isoformat() if rep.created_at else None,
        "updated_at": rep.updated_at.isoformat() if rep.updated_at else None,
    }

def get_sales_reps_tool(db: Session, limit: int = 20) -> dict:
    stmt = (
        select(SalesRep)
        .order_by(SalesRep.name.asc())
        .limit(limit)
    )

    reps = list(db.scalars(stmt).all())

    return {
        "count": len(reps),
        "items": [_serialize_sales_rep(rep) for rep in reps],
    }

def get_sales_rep_client_counts_tool(db: Session) -> dict:
    stmt = (
        select(
            SalesRep.id,
            SalesRep.name,
            func.count(Client.id).label("clients_count"),
        )
        .outerjoin(Client, Client.sales_rep_id == SalesRep.id)
        .group_by(SalesRep.id, SalesRep.name)
        .order_by(func.count(Client.id).desc(), SalesRep.name.asc())
    )

    rows = db.execute(stmt).all()

    return {
        "items": [
            {
                "sales_rep_id": sales_rep_id,
                "sales_rep_name": name,
                "clients_count": clients_count,
            }
            for sales_rep_id, name, clients_count in rows
        ]
    }

def get_sales_rep_order_counts_tool(db: Session) -> dict:
    stmt = (
        select(
            SalesRep.id,
            SalesRep.name,
            func.count(Order.id).label("orders_count"),
        )
        .outerjoin(Order, Order.sales_rep_id == SalesRep.id)
        .group_by(SalesRep.id, SalesRep.name)
        .order_by(func.count(Order.id).desc(), SalesRep.name.asc())
    )

    rows = db.execute(stmt).all()

    return {
        "items": [
            {
                "sales_rep_id": sales_rep_id,
                "sales_rep_name": name,
                "orders_count": orders_count,
            }
            for sales_rep_id, name, orders_count in rows
        ]
    }

def get_sales_rep_performance_tool(db: Session) -> dict:
    stmt = (
        select(
            SalesRep.id,
            SalesRep.name,
            func.count(Order.id).label("orders_count"),
            func.coalesce(func.sum(Order.total_amount), 0).label("total_amount"),
            func.coalesce(func.sum(Order.margin_amount), 0).label("total_margin"),
        )
        .outerjoin(Order, Order.sales_rep_id == SalesRep.id)
        .group_by(SalesRep.id, SalesRep.name)
        .order_by(func.coalesce(func.sum(Order.total_amount), 0).desc(), SalesRep.name.asc())
    )

    rows = db.execute(stmt).all()

    return {
        "items": [
            {
                "sales_rep_id": sales_rep_id,
                "sales_rep_name": name,
                "orders_count": orders_count,
                "total_amount": float(total_amount),
                "total_margin": float(total_margin),
            }
            for sales_rep_id, name, orders_count, total_amount, total_margin in rows
        ]
    }

def get_sales_team_overview_tool(db: Session) -> dict:
    total_sales_reps = db.scalar(select(func.count()).select_from(SalesRep)) or 0
    active_sales_reps = db.scalar(
        select(func.count()).select_from(SalesRep).where(SalesRep.is_active.is_(True))
    ) or 0
    inactive_sales_reps = db.scalar(
        select(func.count()).select_from(SalesRep).where(SalesRep.is_active.is_(False))
    ) or 0
    superusers = db.scalar(
        select(func.count()).select_from(SalesRep).where(SalesRep.is_superuser.is_(True))
    ) or 0

    return {
        "totals": {
            "sales_reps_total": total_sales_reps,
            "active_sales_reps": active_sales_reps,
            "inactive_sales_reps": inactive_sales_reps,
            "superusers": superusers,
        }
    }