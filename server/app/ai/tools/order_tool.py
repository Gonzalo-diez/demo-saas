from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from app.models.order_model import Order

def _serialize_order(order: Order) -> dict:
    return {
        "id": order.id,
        "status": order.status,
        "client_id": order.client_id,
        "client_name": order.client.name if order.client else None,
        "client_branch_id": order.client_branch_id,
        "client_branch_name": order.client_branch.name if order.client_branch else None,
        "client_branch_city": order.client_branch.city if order.client_branch else None,
        "sales_rep_id": order.sales_rep_id,
        "sales_rep_name": order.sales_rep.name if order.sales_rep else None,
        "items_count": len(order.items) if order.items else 0,
        "total_cost": float(order.total_cost) if order.total_cost is not None else None,
        "total_amount": float(order.total_amount) if order.total_amount is not None else None,
        "margin_amount": float(order.margin_amount) if order.margin_amount is not None else None,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }

def get_recent_orders_tool(db: Session, limit: int = 10) -> dict:
    stmt = (
        select(Order)
        .options(
            selectinload(Order.items),
            selectinload(Order.client),
            selectinload(Order.client_branch),
            selectinload(Order.sales_rep),
        )
        .order_by(Order.created_at.desc())
        .limit(limit)
    )

    orders = list(db.scalars(stmt).all())

    return {
        "count": len(orders),
        "items": [_serialize_order(order) for order in orders],
    }

def get_pending_orders_tool(db: Session, limit: int = 10) -> dict:
    stmt = (
        select(Order)
        .options(
            selectinload(Order.items),
            selectinload(Order.client),
            selectinload(Order.client_branch),
            selectinload(Order.sales_rep),
        )
        .where(Order.status == "pending")
        .order_by(Order.created_at.desc())
        .limit(limit)
    )

    orders = list(db.scalars(stmt).all())

    return {
        "count": len(orders),
        "items": [_serialize_order(order) for order in orders],
    }

def get_orders_by_status_tool(db: Session, status: str, limit: int = 20) -> dict:
    stmt = (
        select(Order)
        .options(
            selectinload(Order.items),
            selectinload(Order.client),
            selectinload(Order.client_branch),
            selectinload(Order.sales_rep),
        )
        .where(Order.status == status)
        .order_by(Order.created_at.desc())
        .limit(limit)
    )

    orders = list(db.scalars(stmt).all())

    return {
        "status": status,
        "count": len(orders),
        "items": [_serialize_order(order) for order in orders],
    }

def get_orders_by_sales_rep_tool(db: Session, sales_rep_id: int, limit: int = 20) -> dict:
    stmt = (
        select(Order)
        .options(
            selectinload(Order.items),
            selectinload(Order.client),
            selectinload(Order.client_branch),
            selectinload(Order.sales_rep),
        )
        .where(Order.sales_rep_id == sales_rep_id)
        .order_by(Order.created_at.desc())
        .limit(limit)
    )

    orders = list(db.scalars(stmt).all())

    return {
        "sales_rep_id": sales_rep_id,
        "count": len(orders),
        "items": [_serialize_order(order) for order in orders],
    }

def get_order_overview_tool(db: Session) -> dict:
    total_orders = db.scalar(select(func.count()).select_from(Order)) or 0

    status_stmt = (
        select(Order.status, func.count(Order.id))
        .group_by(Order.status)
        .order_by(func.count(Order.id).desc(), Order.status.asc())
    )
    by_status = [
        {"status": status, "count": count}
        for status, count in db.execute(status_stmt).all()
    ]

    total_amount_sum = db.scalar(select(func.sum(Order.total_amount))) or 0
    total_cost_sum = db.scalar(select(func.sum(Order.total_cost))) or 0
    total_margin_sum = db.scalar(select(func.sum(Order.margin_amount))) or 0

    return {
        "totals": {
            "orders_total": total_orders,
            "total_amount_sum": float(total_amount_sum),
            "total_cost_sum": float(total_cost_sum),
            "total_margin_sum": float(total_margin_sum),
        },
        "by_status": by_status,
    }