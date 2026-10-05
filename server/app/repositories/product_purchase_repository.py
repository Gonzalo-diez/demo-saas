from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.product_purchase_model import ProductPurchase


class ProductPurchaseRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, purchase: ProductPurchase) -> ProductPurchase:
        self.db.add(purchase)
        self.db.flush()
        return purchase

    def list_for_product(self, product_id: int, *, page: int, page_size: int):
        base = select(ProductPurchase).where(ProductPurchase.product_id == product_id)
        total = self.db.scalar(
            select(func.count()).select_from(base.subquery())
        ) or 0
        items = self.db.scalars(
            base.order_by(ProductPurchase.purchase_date.desc(), ProductPurchase.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return items, total

    def summary_for_product(self, product_id: int, today: date) -> dict:
        row = self.db.execute(
            select(
                func.count(ProductPurchase.id),
                func.coalesce(func.sum(ProductPurchase.quantity), 0),
                func.coalesce(
                    func.sum(ProductPurchase.quantity * ProductPurchase.unit_cost), 0
                ),
                func.min(ProductPurchase.unit_cost),
                func.max(ProductPurchase.unit_cost),
            ).where(ProductPurchase.product_id == product_id)
        ).one()
        count, total_qty, total_cost, min_cost, max_cost = row

        last = self.db.scalars(
            select(ProductPurchase.unit_cost)
            .where(ProductPurchase.product_id == product_id)
            .order_by(ProductPurchase.purchase_date.desc(), ProductPurchase.id.desc())
            .limit(1)
        ).first()

        next_expiry = self.db.scalar(
            select(func.min(ProductPurchase.expiry_date)).where(
                ProductPurchase.product_id == product_id,
                ProductPurchase.expiry_date >= today,
            )
        )
        return {
            "count": count,
            "total_quantity": int(total_qty or 0),
            "total_cost": total_cost,
            "min_cost": min_cost,
            "max_cost": max_cost,
            "last_cost": last,
            "next_expiry_date": next_expiry,
        }
