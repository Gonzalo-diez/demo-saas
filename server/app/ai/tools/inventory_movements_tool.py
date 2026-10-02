from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.inventory_movement_model import InventoryMovement
from app.models.product_model import Product


def _serialize_movement(m: InventoryMovement) -> dict:
    return {
        "id": m.id,
        "product_id": m.product_id,
        "product_name": m.product.name if m.product else None,
        "product_sku": m.product.sku if m.product else None,
        "movement_type": m.movement_type,
        "quantity": m.quantity,
        "stock_before": m.stock_before,
        "stock_after": m.stock_after,
        "unit_cost": float(m.unit_cost) if m.unit_cost is not None else None,
        "reference_type": m.reference_type,
        "reference_id": m.reference_id,
        "notes": m.notes,
        "created_by_id": m.created_by,
        "created_by_name": m.creator.name if m.creator else None,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


def get_recent_inventory_movements_tool(db: Session, limit: int = 10) -> dict:
    stmt = (
        select(InventoryMovement)
        .options(
            joinedload(InventoryMovement.product),
            joinedload(InventoryMovement.creator),
        )
        .order_by(InventoryMovement.created_at.desc())
        .limit(limit)
    )

    movements = list(db.scalars(stmt).all())

    return {
        "count": len(movements),
        "items": [_serialize_movement(m) for m in movements],
    }


def get_inventory_movement_overview_tool(db: Session) -> dict:
    total = db.scalar(select(func.count()).select_from(InventoryMovement)) or 0

    by_type_stmt = (
        select(InventoryMovement.movement_type, func.count(InventoryMovement.id))
        .group_by(InventoryMovement.movement_type)
        .order_by(func.count(InventoryMovement.id).desc())
    )
    by_type = [
        {"movement_type": mt, "count": count}
        for mt, count in db.execute(by_type_stmt).all()
    ]

    # Productos con más movimientos (señal de alta rotación o problemas de stock)
    top_products_stmt = (
        select(
            Product.id,
            Product.name,
            Product.sku,
            func.count(InventoryMovement.id).label("movement_count"),
        )
        .join(InventoryMovement, InventoryMovement.product_id == Product.id)
        .group_by(Product.id, Product.name, Product.sku)
        .order_by(func.count(InventoryMovement.id).desc())
        .limit(10)
    )
    top_products = [
        {"product_id": pid, "product_name": name, "sku": sku, "movement_count": count}
        for pid, name, sku, count in db.execute(top_products_stmt).all()
    ]

    return {
        "total_movements": total,
        "by_movement_type": by_type,
        "top_products_by_movement_count": top_products,
    }