from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.models.analytics_daily_model import AnalyticsDaily
from app.analytics.models.analytics_product_daily_model import AnalyticsProductDaily
from app.analytics.models.analytics_sales_rep_daily_model import AnalyticsSalesRepDaily
from app.analytics.models.analytics_zone_product_daily_model import AnalyticsZoneProductDaily
from app.analytics.models.analytics_client_daily_model import AnalyticsClientDaily
from app.models.client_model import Client
from app.models.product_model import Product
from app.models.sales_rep_model import SalesRep


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_date(value: str | None, fallback: date) -> date:
    """Convierte string ISO a date, devuelve fallback si None o inválido."""
    if value is None:
        return fallback
    try:
        return date.fromisoformat(value)
    except ValueError:
        return fallback


# ─────────────────────────────────────────────────────────────────────────────
# 1. Resumen global diario
# ─────────────────────────────────────────────────────────────────────────────

def get_daily_summary_tool(db: Session, target_date: str | None = None) -> dict:
    """
    Resumen global del negocio para una fecha específica.
    Si no se pasa fecha, usa el día de ayer (último día con datos completos).
    """
    resolved_date = _parse_date(target_date, date.today() - timedelta(days=1))

    row = db.scalar(
        select(AnalyticsDaily).where(AnalyticsDaily.date == resolved_date)
    )

    if row is None:
        return {
            "date": resolved_date.isoformat(),
            "available": False,
            "message": f"No hay datos de analytics para {resolved_date.isoformat()}. "
                       "Verificá que el job de agregación se haya ejecutado.",
        }

    return {
        "date": row.date.isoformat(),
        "available": True,
        "total_orders": row.total_orders,
        "total_clients": row.total_clients,
        "total_products_sold": row.total_products_sold,
        "revenue_generated": float(row.revenue_generated),
        "cost_generated": float(row.cost_generated),
        "margin_generated": float(row.margin_generated),
        "average_ticket": float(row.average_ticket),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. Top productos por revenue en un rango de fechas
# ─────────────────────────────────────────────────────────────────────────────

def get_top_products_tool(
    db: Session,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 10,
) -> dict:
    """
    Ranking de productos más vendidos por revenue en un rango de fechas.
    Si no se pasan fechas, usa los últimos 30 días.
    """
    today = date.today()
    resolved_start = _parse_date(start_date, today - timedelta(days=30))
    resolved_end = _parse_date(end_date, today - timedelta(days=1))

    stmt = (
        select(
            AnalyticsProductDaily.product_id,
            Product.name.label("product_name"),
            Product.sku.label("product_sku"),
            Product.brand.label("product_brand"),
            Product.category.label("product_category"),
            func.sum(AnalyticsProductDaily.quantity_sold).label("total_quantity"),
            func.sum(AnalyticsProductDaily.revenue_generated).label("total_revenue"),
            func.sum(AnalyticsProductDaily.cost_generated).label("total_cost"),
            func.sum(AnalyticsProductDaily.margin_generated).label("total_margin"),
        )
        .join(Product, Product.id == AnalyticsProductDaily.product_id)
        .where(AnalyticsProductDaily.date >= resolved_start)
        .where(AnalyticsProductDaily.date <= resolved_end)
        .group_by(
            AnalyticsProductDaily.product_id,
            Product.name,
            Product.sku,
            Product.brand,
            Product.category,
        )
        .order_by(func.sum(AnalyticsProductDaily.revenue_generated).desc())
        .limit(limit)
    )

    rows = db.execute(stmt).all()

    return {
        "start_date": resolved_start.isoformat(),
        "end_date": resolved_end.isoformat(),
        "count": len(rows),
        "ranked_by": "revenue_generated",
        "items": [
            {
                "rank": i + 1,
                "product_id": row.product_id,
                "product_name": row.product_name,
                "product_sku": row.product_sku,
                "product_brand": row.product_brand,
                "product_category": row.product_category,
                "total_quantity": row.total_quantity,
                "total_revenue": float(row.total_revenue),
                "total_cost": float(row.total_cost),
                "total_margin": float(row.total_margin),
                "margin_pct": round(
                    float(row.total_margin) / float(row.total_revenue) * 100, 1
                ) if float(row.total_revenue) > 0 else 0.0,
            }
            for i, row in enumerate(rows)
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Top vendedores por revenue en un rango de fechas
# ─────────────────────────────────────────────────────────────────────────────

def get_top_sales_reps_tool(
    db: Session,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 10,
) -> dict:
    """
    Ranking de vendedores por revenue generado en un rango de fechas.
    Si no se pasan fechas, usa los últimos 30 días.
    """
    today = date.today()
    resolved_start = _parse_date(start_date, today - timedelta(days=30))
    resolved_end = _parse_date(end_date, today - timedelta(days=1))

    stmt = (
        select(
            AnalyticsSalesRepDaily.sales_rep_id,
            SalesRep.name.label("sales_rep_name"),
            SalesRep.email.label("sales_rep_email"),
            func.sum(AnalyticsSalesRepDaily.total_orders).label("total_orders"),
            func.sum(AnalyticsSalesRepDaily.total_clients).label("total_clients"),
            func.sum(AnalyticsSalesRepDaily.total_products_sold).label("total_products_sold"),
            func.sum(AnalyticsSalesRepDaily.revenue_generated).label("total_revenue"),
            func.sum(AnalyticsSalesRepDaily.cost_generated).label("total_cost"),
            func.sum(AnalyticsSalesRepDaily.margin_generated).label("total_margin"),
        )
        .join(SalesRep, SalesRep.id == AnalyticsSalesRepDaily.sales_rep_id)
        .where(AnalyticsSalesRepDaily.date >= resolved_start)
        .where(AnalyticsSalesRepDaily.date <= resolved_end)
        .group_by(
            AnalyticsSalesRepDaily.sales_rep_id,
            SalesRep.name,
            SalesRep.email,
        )
        .order_by(func.sum(AnalyticsSalesRepDaily.revenue_generated).desc())
        .limit(limit)
    )

    rows = db.execute(stmt).all()

    return {
        "start_date": resolved_start.isoformat(),
        "end_date": resolved_end.isoformat(),
        "count": len(rows),
        "ranked_by": "revenue_generated",
        "items": [
            {
                "rank": i + 1,
                "sales_rep_id": row.sales_rep_id,
                "sales_rep_name": row.sales_rep_name,
                "sales_rep_email": row.sales_rep_email,
                "total_orders": row.total_orders,
                "total_clients": row.total_clients,
                "total_products_sold": row.total_products_sold,
                "total_revenue": float(row.total_revenue),
                "total_cost": float(row.total_cost),
                "total_margin": float(row.total_margin),
                "margin_pct": round(
                    float(row.total_margin) / float(row.total_revenue) * 100, 1
                ) if float(row.total_revenue) > 0 else 0.0,
            }
            for i, row in enumerate(rows)
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. Tendencia de un producto en el tiempo
# ─────────────────────────────────────────────────────────────────────────────

def get_product_trend_tool(
    db: Session,
    product_id: int,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """
    Evolución diaria de métricas de un producto específico en un rango de fechas.
    Si no se pasan fechas, usa los últimos 30 días.
    """
    today = date.today()
    resolved_start = _parse_date(start_date, today - timedelta(days=30))
    resolved_end = _parse_date(end_date, today - timedelta(days=1))

    product = db.scalar(select(Product).where(Product.id == product_id))
    if product is None:
        return {
            "product_id": product_id,
            "available": False,
            "message": f"Producto con id={product_id} no encontrado.",
        }

    stmt = (
        select(AnalyticsProductDaily)
        .where(AnalyticsProductDaily.product_id == product_id)
        .where(AnalyticsProductDaily.date >= resolved_start)
        .where(AnalyticsProductDaily.date <= resolved_end)
        .order_by(AnalyticsProductDaily.date.asc())
    )

    rows = list(db.scalars(stmt).all())

    total_revenue = sum(float(r.revenue_generated) for r in rows)
    total_quantity = sum(r.quantity_sold for r in rows)
    total_margin = sum(float(r.margin_generated) for r in rows)

    return {
        "product_id": product_id,
        "product_name": product.name,
        "product_sku": product.sku,
        "start_date": resolved_start.isoformat(),
        "end_date": resolved_end.isoformat(),
        "days_with_data": len(rows),
        "totals": {
            "total_quantity": total_quantity,
            "total_revenue": total_revenue,
            "total_margin": total_margin,
            "margin_pct": round(total_margin / total_revenue * 100, 1) if total_revenue > 0 else 0.0,
        },
        "daily": [
            {
                "date": r.date.isoformat(),
                "quantity_sold": r.quantity_sold,
                "revenue_generated": float(r.revenue_generated),
                "cost_generated": float(r.cost_generated),
                "margin_generated": float(r.margin_generated),
            }
            for r in rows
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. Distribución geográfica de ventas por zona H3
# ─────────────────────────────────────────────────────────────────────────────

def get_zone_sales_tool(
    db: Session,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 20,
) -> dict:
    """
    Ranking de zonas geográficas (H3) por revenue en un rango de fechas.
    Útil para detectar zonas de alta/baja cobertura territorial.
    Si no se pasan fechas, usa los últimos 30 días.
    """
    today = date.today()
    resolved_start = _parse_date(start_date, today - timedelta(days=30))
    resolved_end = _parse_date(end_date, today - timedelta(days=1))

    stmt = (
        select(
            AnalyticsZoneProductDaily.h3_index,
            func.sum(AnalyticsZoneProductDaily.quantity_sold).label("total_quantity"),
            func.sum(AnalyticsZoneProductDaily.revenue_generated).label("total_revenue"),
            func.sum(AnalyticsZoneProductDaily.margin_generated).label("total_margin"),
            func.sum(AnalyticsZoneProductDaily.unique_clients).label("total_unique_clients"),
            func.count(AnalyticsZoneProductDaily.product_id.distinct()).label("distinct_products"),
        )
        .where(AnalyticsZoneProductDaily.date >= resolved_start)
        .where(AnalyticsZoneProductDaily.date <= resolved_end)
        .group_by(AnalyticsZoneProductDaily.h3_index)
        .order_by(func.sum(AnalyticsZoneProductDaily.revenue_generated).desc())
        .limit(limit)
    )

    rows = db.execute(stmt).all()

    return {
        "start_date": resolved_start.isoformat(),
        "end_date": resolved_end.isoformat(),
        "count": len(rows),
        "ranked_by": "revenue_generated",
        "items": [
            {
                "rank": i + 1,
                "h3_index": row.h3_index,
                "total_quantity": row.total_quantity,
                "total_revenue": float(row.total_revenue),
                "total_margin": float(row.total_margin),
                "total_unique_clients": row.total_unique_clients,
                "distinct_products": row.distinct_products,
                "margin_pct": round(
                    float(row.total_margin) / float(row.total_revenue) * 100, 1
                ) if float(row.total_revenue) > 0 else 0.0,
            }
            for i, row in enumerate(rows)
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 6. Resumen de período (rango libre de analytics_daily agregados)
# ─────────────────────────────────────────────────────────────────────────────

def get_period_summary_tool(
    db: Session,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """
    Resumen acumulado del negocio para un rango de fechas.
    Suma todos los días del rango desde analytics_daily.
    Si no se pasan fechas, usa los últimos 30 días.
    """
    today = date.today()
    resolved_start = _parse_date(start_date, today - timedelta(days=30))
    resolved_end = _parse_date(end_date, today - timedelta(days=1))

    stmt = (
        select(
            func.count(AnalyticsDaily.id).label("days_with_data"),
            func.sum(AnalyticsDaily.total_orders).label("total_orders"),
            func.sum(AnalyticsDaily.total_clients).label("total_clients"),
            func.sum(AnalyticsDaily.total_products_sold).label("total_products_sold"),
            func.sum(AnalyticsDaily.revenue_generated).label("total_revenue"),
            func.sum(AnalyticsDaily.cost_generated).label("total_cost"),
            func.sum(AnalyticsDaily.margin_generated).label("total_margin"),
            func.avg(AnalyticsDaily.average_ticket).label("avg_ticket"),
        )
        .where(AnalyticsDaily.date >= resolved_start)
        .where(AnalyticsDaily.date <= resolved_end)
    )

    row = db.execute(stmt).one()

    if not row.days_with_data:
        return {
            "start_date": resolved_start.isoformat(),
            "end_date": resolved_end.isoformat(),
            "available": False,
            "message": "No hay datos de analytics para el período indicado.",
        }

    total_revenue = float(row.total_revenue or 0)
    total_margin = float(row.total_margin or 0)

    return {
        "start_date": resolved_start.isoformat(),
        "end_date": resolved_end.isoformat(),
        "available": True,
        "days_with_data": row.days_with_data,
        "total_orders": row.total_orders or 0,
        "total_clients": row.total_clients or 0,
        "total_products_sold": row.total_products_sold or 0,
        "total_revenue": total_revenue,
        "total_cost": float(row.total_cost or 0),
        "total_margin": total_margin,
        "margin_pct": round(total_margin / total_revenue * 100, 1) if total_revenue > 0 else 0.0,
        "avg_ticket": round(float(row.avg_ticket or 0), 2),
    }
    
# ─────────────────────────────────────────────────────────────────────────────
# 7. Top clientes por revenue en un rango de fechas
# ─────────────────────────────────────────────────────────────────────────────
    
def get_top_clients_tool(
    db: Session,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 10,
) -> dict:
    """
    Ranking de clientes por revenue generado en un rango de fechas.
    Si no se pasan fechas, usa los últimos 30 días.
    """
    today = date.today()
    resolved_start = _parse_date(start_date, today - timedelta(days=30))
    resolved_end = _parse_date(end_date, today - timedelta(days=1))

    stmt = (
        select(
            AnalyticsClientDaily.client_id,
            Client.name.label("client_name"),
            func.sum(AnalyticsClientDaily.total_orders).label("total_orders"),
            func.sum(AnalyticsClientDaily.revenue_generated).label("total_revenue"),
            func.sum(AnalyticsClientDaily.cost_generated).label("total_cost"),
            func.sum(AnalyticsClientDaily.margin_generated).label("total_margin"),
        )
        .join(Client, Client.id == AnalyticsClientDaily.client_id)
        .where(AnalyticsClientDaily.date >= resolved_start)
        .where(AnalyticsClientDaily.date <= resolved_end)
        .group_by(
            AnalyticsClientDaily.client_id,
            Client.name,
        )
        .order_by(func.sum(AnalyticsClientDaily.revenue_generated).desc())
        .limit(limit)
    )

    rows = db.execute(stmt).all()

    return {
        "start_date": resolved_start.isoformat(),
        "end_date": resolved_end.isoformat(),
        "count": len(rows),
        "ranked_by": "revenue_generated",
        "items": [
            {
                "rank": i + 1,
                "client_id": row.client_id,
                "client_name": row.client_name,
                "total_orders": row.total_orders,
                "total_revenue": float(row.total_revenue),
                "total_cost": float(row.total_cost),
                "total_margin": float(row.total_margin),
                "margin_pct": round(
                    float(row.total_margin) / float(row.total_revenue) * 100, 1
                ) if float(row.total_revenue) > 0 else 0.0,
            }
            for i, row in enumerate(rows)
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 8. Tendencia de un cliente en el tiempo
# ─────────────────────────────────────────────────────────────────────────────

def get_client_trend_tool(
    db: Session,
    client_id: int,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """
    Evolución diaria de métricas de un cliente específico en un rango de fechas.
    Incluye órdenes, revenue, margen y productos comprados por día.
    Si no se pasan fechas, usa los últimos 30 días.
    """
    today = date.today()
    resolved_start = _parse_date(start_date, today - timedelta(days=30))
    resolved_end = _parse_date(end_date, today - timedelta(days=1))

    client = db.scalar(select(Client).where(Client.id == client_id))
    if client is None:
        return {
            "client_id": client_id,
            "available": False,
            "message": f"Cliente con id={client_id} no encontrado.",
        }

    stmt = (
        select(AnalyticsClientDaily)
        .where(AnalyticsClientDaily.client_id == client_id)
        .where(AnalyticsClientDaily.date >= resolved_start)
        .where(AnalyticsClientDaily.date <= resolved_end)
        .order_by(AnalyticsClientDaily.date.asc())
    )

    rows = list(db.scalars(stmt).all())

    total_revenue = sum(float(r.revenue_generated) for r in rows)
    total_orders = sum(r.total_orders for r in rows)
    total_margin = sum(float(r.margin_generated) for r in rows)

    return {
        "client_id": client_id,
        "client_name": client.name,
        "start_date": resolved_start.isoformat(),
        "end_date": resolved_end.isoformat(),
        "days_with_data": len(rows),
        "totals": {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "total_margin": total_margin,
            "margin_pct": round(total_margin / total_revenue * 100, 1) if total_revenue > 0 else 0.0,
        },
        "daily": [
            {
                "date": r.date.isoformat(),
                "total_orders": r.total_orders,
                "revenue_generated": float(r.revenue_generated),
                "cost_generated": float(r.cost_generated),
                "margin_generated": float(r.margin_generated),
                "unique_products_count": r.unique_products_count,
                "products_bought": r.products_bought,
            }
            for r in rows
        ],
    }