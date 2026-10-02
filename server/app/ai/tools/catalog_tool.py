from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.models.product_model import Product

def _serialize_product(product: Product) -> dict:
    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "brand": product.brand,
        "category": product.category,
        "stock_current": product.stock_current,
        "stock_min": product.stock_min,
        "unit_cost": float(product.unit_cost),
        "unit_price": float(product.unit_price),
        "is_active": product.is_active,
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
    }

def get_low_stock_products_tool(db: Session, limit: int = 10) -> dict:
    stmt = (
        select(Product)
        .where(Product.is_active.is_(True))
        .where(Product.stock_current <= Product.stock_min)
        .order_by(Product.stock_current.asc(), Product.stock_min.asc(), Product.name.asc())
        .limit(limit)
    )
    products = list(db.scalars(stmt).all())

    return {
        "count": len(products),
        "items": [_serialize_product(product) for product in products],
    }

def get_inactive_products_tool(db: Session, limit: int = 10) -> dict:
    stmt = (
        select(Product)
        .where(Product.is_active.is_(False))
        .order_by(Product.updated_at.desc(), Product.name.asc())
        .limit(limit)
    )
    products = list(db.scalars(stmt).all())

    return {
        "count": len(products),
        "items": [_serialize_product(product) for product in products],
    }

def search_products_tool(db: Session, query: str, limit: int = 10) -> dict:
    search_term = f"%{query.strip()}%"

    stmt = (
        select(Product)
        .where(
            or_(
                Product.name.ilike(search_term),
                Product.sku.ilike(search_term),
                Product.brand.ilike(search_term),
                Product.category.ilike(search_term),
            )
        )
        .order_by(Product.name.asc())
        .limit(limit)
    )

    products = list(db.scalars(stmt).all())

    return {
        "query": query,
        "count": len(products),
        "items": [_serialize_product(product) for product in products],
    }

def get_products_by_category_tool(db: Session, category: str, limit: int = 20) -> dict:
    stmt = (
        select(Product)
        .where(Product.category.ilike(category.strip()))
        .order_by(Product.name.asc())
        .limit(limit)
    )

    products = list(db.scalars(stmt).all())

    return {
        "category": category,
        "count": len(products),
        "items": [_serialize_product(product) for product in products],
    }

def get_product_catalog_overview_tool(db: Session) -> dict:
    total_products = db.scalar(select(func.count()).select_from(Product)) or 0
    active_products = db.scalar(
        select(func.count()).select_from(Product).where(Product.is_active.is_(True))
    ) or 0
    inactive_products = db.scalar(
        select(func.count()).select_from(Product).where(Product.is_active.is_(False))
    ) or 0
    low_stock_products = db.scalar(
        select(func.count())
        .select_from(Product)
        .where(Product.is_active.is_(True))
        .where(Product.stock_current <= Product.stock_min)
    ) or 0

    categories_stmt = (
        select(Product.category, func.count(Product.id))
        .where(Product.category.is_not(None))
        .group_by(Product.category)
        .order_by(func.count(Product.id).desc(), Product.category.asc())
        .limit(10)
    )
    categories = [
        {"category": category, "count": count}
        for category, count in db.execute(categories_stmt).all()
    ]

    brands_stmt = (
        select(Product.brand, func.count(Product.id))
        .where(Product.brand.is_not(None))
        .group_by(Product.brand)
        .order_by(func.count(Product.id).desc(), Product.brand.asc())
        .limit(10)
    )
    brands = [
        {"brand": brand, "count": count}
        for brand, count in db.execute(brands_stmt).all()
    ]

    return {
        "totals": {
            "products_total": total_products,
            "active_products": active_products,
            "inactive_products": inactive_products,
            "low_stock_products": low_stock_products,
        },
        "top_categories": categories,
        "top_brands": brands,
    }