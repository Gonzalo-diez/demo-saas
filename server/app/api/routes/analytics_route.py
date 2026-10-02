from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_active_user, get_public_tenant
from app.core.scheduler import scheduler
from app.db.base import get_db, get_db_with_commit
from app.models.sales_rep_model import SalesRep
from app.models.tenant_model import Tenant
from app.analytics.constants.event_type_constant import AnalyticsEventType
from app.analytics.models.analytics_product_daily_model import AnalyticsProductDaily
from app.analytics.models.analytics_client_daily_model import AnalyticsClientDaily
from app.analytics.models.analytics_sales_rep_daily_model import AnalyticsSalesRepDaily
from app.analytics.schemas.analytics_catalog_event_schema import (
    AnalyticsCatalogEventCreate,
    AnalyticsCatalogEventRead,
)
from app.analytics.schemas.analytics_daily_schema import AnalyticsDailyRead
from app.analytics.schemas.analytics_product_daily_schema import AnalyticsProductDailyRead
from app.analytics.schemas.analytics_client_daily_schema import AnalyticsClientDailyRead
from app.analytics.schemas.analytics_sales_rep_daily_schema import AnalyticsSalesRepDailyRead
from app.analytics.services.analytics_catalog_event_service import AnalyticsCatalogEventService
from app.analytics.services.analytics_daily_service import AnalyticsDailyService
from app.analytics.services.analytics_product_daily_service import AnalyticsProductDailyService
from app.analytics.services.analytics_client_daily_service import AnalyticsClientDailyService
from app.analytics.services.analytics_sales_rep_daily_service import AnalyticsSalesRepDailyService
from app.analytics.services.analytics_zone_product_daily_service import AnalyticsZoneProductDailyService
from app.analytics.jobs.run_daily_aggregations import RunDailyAggregationsJob

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)

@router.get(
    "/events",
    response_model=List[AnalyticsCatalogEventRead],
    summary="Lista eventos con filtros",
)
def list_catalog_events(
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    event_type: Optional[AnalyticsEventType] = Query(default=None),
    product_id: Optional[int] = Query(default=None, gt=0),
    sales_rep_id: Optional[int] = Query(default=None, gt=0),
    visitor_id: Optional[str] = Query(default=None, max_length=128),
    session_id: Optional[str] = Query(default=None, max_length=128),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    """
    Lista eventos con filtros opcionales. Solo accesible con auth (backoffice/admin).
    """
    service = AnalyticsCatalogEventService()
    return service.list_events(
        db,
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        product_id=product_id,
        sales_rep_id=sales_rep_id,
        visitor_id=visitor_id,
        session_id=session_id,
        limit=limit,
        offset=offset,
    )

@router.get(
    "/events/count",
    response_model=dict,
    summary="Cuenta eventos según filtros",
)
def count_catalog_events(
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    event_type: Optional[AnalyticsEventType] = Query(default=None),
    product_id: Optional[int] = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    """
    Cuenta eventos según filtros. Útil para dashboards sin cargar los registros.
    """
    service = AnalyticsCatalogEventService()
    total = service.count_events(
        db,
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        product_id=product_id,
    )
    return {"total": total}

@router.get(
    "/events/stats",
    response_model=dict,
    summary="Conteo de eventos agrupado por tipo",
)
def get_catalog_events_stats(
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    """
    Devuelve un dict {event_type: count} para el rango dado.
    Si no se pasa rango, cuenta todo el histórico.

    Ejemplo de respuesta:
    {
        "product_view": 1240,
        "product_click": 320,
        "product_search": 88,
        "sales_rep_view": 54,
        "sales_rep_contact": 12,
        "catalog_open": 430
    }
    """
    service = AnalyticsCatalogEventService()
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    return {
        event_type.value: service.count_events(
            db,
            start_date=start_dt,
            end_date=end_dt,
            event_type=event_type,
        )
        for event_type in AnalyticsEventType
    }

@router.get(
    "/events/{event_id}",
    response_model=AnalyticsCatalogEventRead,
    summary="Obtiene un evento por ID",
)
def get_catalog_event(
    event_id: int,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = AnalyticsCatalogEventService()
    event = service.get_event(db, event_id)
    if not event:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado",
        )
    return event

@router.post(
    "/events",
    response_model=AnalyticsCatalogEventRead,
    status_code=http_status.HTTP_201_CREATED,
    summary="Registra un evento individual del catálogo",
)
def create_catalog_event(
    event_in: AnalyticsCatalogEventCreate,
    db: Session = Depends(get_db_with_commit),
    _tenant: Tenant = Depends(get_public_tenant),
):
    """
    Sin login obligatorio — lo llama el frontend público (catálogo del vendedor).
    El tenant sale del token (si hay) o del header X-Tenant-Slug.
    """
    service = AnalyticsCatalogEventService()
    event = service.create_event(db, event_in=event_in)
    return event

@router.post(
    "/events/bulk",
    status_code=http_status.HTTP_204_NO_CONTENT,
    summary="Registra múltiples eventos en una sola llamada",
)
def create_catalog_events_bulk(
    events_in: List[AnalyticsCatalogEventCreate],
    db: Session = Depends(get_db_with_commit),
    _tenant: Tenant = Depends(get_public_tenant),
):
    """
    Útil para flush por lote desde el frontend.
    Sin auth — mismo caso que el endpoint individual.
    """
    service = AnalyticsCatalogEventService()
    service.create_events_bulk(db, events_in=events_in)

@router.get(
    "/daily",
    response_model=AnalyticsDailyRead,
    summary="Snapshot global del día",
)
def get_analytics_daily(
    target_date: date = Query(...),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    """
    Devuelve el snapshot global (orders, clientes, revenue, margen, ticket promedio)
    para una fecha. Si no existe el registro devuelve 404 — ejecutá /aggregate primero.
    """
    service = AnalyticsDailyService()
    record = service.repo.get_by_date(db, target_date)
    if not record:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Sin datos para {target_date}. Ejecutá /analytics/aggregate primero.",
        )
    return AnalyticsDailyRead.model_validate(record)

@router.get(
    "/daily/range",
    response_model=List[AnalyticsDailyRead],
    summary="Histórico global en rango de fechas",
)
def get_analytics_daily_range(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    limit: int = Query(default=31, ge=1, le=365),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    """
    Serie temporal del resumen global. Útil para gráficos de tendencia.
    """
    start_date = start_date.date()
    end_date = end_date.date()

    service = AnalyticsDailyService()
    records = service.repo.list_range(
        db,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    return [AnalyticsDailyRead.model_validate(r) for r in records]

@router.get(
    "/products/daily",
    summary="Métricas de todos los productos para una fecha",
)
def get_product_daily(
    target_date: date = Query(...),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = AnalyticsProductDailyService(db)
    return service.get_daily_metrics(target_date=target_date)


@router.get(
    "/products/daily/{product_id}",
    summary="Métricas de un producto para una fecha",
)
def get_product_daily_by_product(
    product_id: int,
    target_date: date = Query(...),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = AnalyticsProductDailyService(db)
    return service.get_product_metrics(
        product_id=product_id,
        target_date=target_date,
    )

@router.get(
    "/products/{product_id}/history",
    response_model=List[AnalyticsProductDailyRead],
    summary="Histórico de un producto en rango de fechas",
)
def get_product_history(
    product_id: int,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    limit: int = Query(default=90, ge=1, le=365),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    start_date = start_date.date()
    end_date = end_date.date()

    service = AnalyticsProductDailyService(db)
    return service.get_product_history(
        product_id=product_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

@router.get(
    "/clients/daily",
    summary="Métricas de todos los clientes para una fecha",
)
def get_client_daily(
    target_date: date = Query(...),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = AnalyticsClientDailyService(db)
    return service.get_daily_metrics(target_date=target_date)


@router.get(
    "/clients/daily/{client_id}",
    summary="Métricas de un cliente para una fecha",
)
def get_client_daily_by_client(
    client_id: int,
    target_date: date = Query(...),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = AnalyticsClientDailyService(db)
    return service.get_client_metrics(
        client_id=client_id,
        target_date=target_date,
    )

@router.get(
    "/clients/{client_id}/history",
    summary="Histórico de un cliente en rango de fechas",
)
def get_client_history(
    client_id: int,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    limit: int = Query(default=90, ge=1, le=365),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    start_date = start_date.date()
    end_date = end_date.date()

    service = AnalyticsClientDailyService(db)
    return service.get_client_history(
        client_id=client_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

@router.get(
    "/sales-reps/daily",
    summary="Métricas de todos los vendedores para una fecha",
)
def get_sales_rep_daily(
    target_date: date = Query(...),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = AnalyticsSalesRepDailyService(db)
    return service.get_daily_metrics(target_date=target_date)

@router.get(
    "/sales-reps/daily/{sales_rep_id}",
    summary="Métricas de un vendedor para una fecha",
)
def get_sales_rep_daily_by_rep(
    sales_rep_id: int,
    target_date: date = Query(...),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = AnalyticsSalesRepDailyService(db)
    return service.get_sales_rep_metrics(
        sales_rep_id=sales_rep_id,
        target_date=target_date,
    )

@router.get(
    "/sales-reps/{sales_rep_id}/history",
    response_model=List[AnalyticsSalesRepDailyRead],
    summary="Histórico de un vendedor en rango de fechas",
)
def get_sales_rep_history(
    sales_rep_id: int,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    limit: int = Query(default=90, ge=1, le=365),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    start_date = start_date.date()
    end_date = end_date.date()

    service = AnalyticsSalesRepDailyService(db)
    return service.get_rep_history(
        sales_rep_id=sales_rep_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

@router.get(
    "/zones/products/daily",
    summary="Métricas de productos por zona para una fecha",
)
def get_zone_product_daily(
    target_date: date = Query(...),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = AnalyticsZoneProductDailyService(db)
    return service.get_daily_metrics(target_date=target_date)


@router.get(
    "/zones/products/daily/{h3_index}",
    summary="Métricas de una zona específica para una fecha",
)
def get_zone_product_daily_by_zone(
    h3_index: str,
    target_date: date = Query(...),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = AnalyticsZoneProductDailyService(db)
    return service.get_zone_metrics(
        h3_index=h3_index,
        target_date=target_date,
    )

@router.get(
    "/rankings/products",
    response_model=List[AnalyticsProductDailyRead],
    summary="Top N productos por revenue o unidades en un rango",
)
def get_top_products(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    order_by: str = Query(default="revenue", pattern="^(revenue|quantity)$"),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    """
    Agrega los snapshots diarios de productos en el rango y devuelve
    los top N ordenados por revenue_generated o quantity_sold.
    """
    start_date = start_date.date()
    end_date = end_date.date()

    sort_col = (
        func.sum(AnalyticsProductDaily.revenue_generated)
        if order_by == "revenue"
        else func.sum(AnalyticsProductDaily.quantity_sold)
    )

    stmt = (
        select(
            AnalyticsProductDaily.product_id,
            func.sum(AnalyticsProductDaily.quantity_sold).label("quantity_sold"),
            func.sum(AnalyticsProductDaily.revenue_generated).label("revenue_generated"),
            func.sum(AnalyticsProductDaily.cost_generated).label("cost_generated"),
            func.sum(AnalyticsProductDaily.margin_generated).label("margin_generated"),
            func.max(AnalyticsProductDaily.date).label("date"),
            func.max(AnalyticsProductDaily.id).label("id"),
            func.max(AnalyticsProductDaily.created_at).label("created_at"),
        )
        .where(AnalyticsProductDaily.date >= start_date)
        .where(AnalyticsProductDaily.date <= end_date)
        .group_by(AnalyticsProductDaily.product_id)
        .order_by(sort_col.desc())
        .limit(limit)
    )

    rows = db.execute(stmt).mappings().all()
    return [AnalyticsProductDailyRead.model_validate(dict(r)) for r in rows]

@router.get(
    "/rankings/clients",
    response_model=List[AnalyticsClientDailyRead],
    summary="Top N clientes por revenue u órdenes en un rango",
)
def get_top_clients(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    order_by: str = Query(default="revenue", pattern="^(revenue|orders)$"),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    """
    Agrega los snapshots diarios de clientes en el rango y devuelve los top N.
    products_bought se devuelve vacío en el ranking; consultá
    /clients/{client_id}/history para el detalle.
    """
    start_date = start_date.date()
    end_date = end_date.date()

    sort_col = (
        func.sum(AnalyticsClientDaily.revenue_generated)
        if order_by == "revenue"
        else func.sum(AnalyticsClientDaily.total_orders)
    )

    stmt = (
        select(
            AnalyticsClientDaily.client_id,
            func.sum(AnalyticsClientDaily.total_orders).label("total_orders"),
            func.sum(AnalyticsClientDaily.revenue_generated).label("revenue_generated"),
            func.sum(AnalyticsClientDaily.cost_generated).label("cost_generated"),
            func.sum(AnalyticsClientDaily.margin_generated).label("margin_generated"),
            func.sum(AnalyticsClientDaily.unique_products_count).label("unique_products_count"),
            func.max(AnalyticsClientDaily.date).label("date"),
            func.max(AnalyticsClientDaily.id).label("id"),
            func.max(AnalyticsClientDaily.created_at).label("created_at"),
        )
        .where(AnalyticsClientDaily.date >= start_date)
        .where(AnalyticsClientDaily.date <= end_date)
        .group_by(AnalyticsClientDaily.client_id)
        .order_by(sort_col.desc())
        .limit(limit)
    )

    rows = db.execute(stmt).mappings().all()
    results = []
    for r in rows:
        data = dict(r)
        data.setdefault("products_bought", [])
        results.append(AnalyticsClientDailyRead.model_validate(data))
    return results

@router.get(
    "/rankings/clients/categories",
    response_model=List[dict],
    summary="Top categorías compradas por clientes en un rango de fechas",
)
def get_top_client_categories(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    client_id: Optional[int] = Query(default=None, gt=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    """
    Agrega el JSONB categories_summary de todos los snapshots en el rango
    y devuelve un ranking de categorías ordenado por amount total.
    Opcionalmente filtrable por client_id para ver el perfil de un cliente específico.
    """
    start_date = start_date.date()
    end_date = end_date.date()

    from sqlalchemy import cast
    from sqlalchemy.dialects.postgresql import JSONB
    from app.analytics.models.analytics_client_daily_model import AnalyticsClientDaily

    stmt = (
        select(AnalyticsClientDaily.categories_summary)
        .where(AnalyticsClientDaily.date >= start_date)
        .where(AnalyticsClientDaily.date <= end_date)
    )
    if client_id is not None:
        stmt = stmt.where(AnalyticsClientDaily.client_id == client_id)

    rows = db.execute(stmt).scalars().all()

    # Merge all categories_summary arrays
    merged: dict[str, dict] = {}
    for summary_list in rows:
        for entry in (summary_list or []):
            cat = entry.get("category") or "Sin categoría"
            qty = int(entry.get("qty", 0))
            amount = float(entry.get("amount", 0))
            unique = int(entry.get("unique_products", 0))

            if cat not in merged:
                merged[cat] = {"category": cat, "qty": 0, "amount": 0.0, "unique_products": 0}

            merged[cat]["qty"] += qty
            merged[cat]["amount"] += amount
            merged[cat]["unique_products"] += unique

    result = sorted(merged.values(), key=lambda x: x["amount"], reverse=True)[:limit]
    # Serialize amount as string for consistency
    for item in result:
        item["amount"] = str(round(item["amount"], 2))

    return result

@router.get(
    "/rankings/sales-reps",
    response_model=List[AnalyticsSalesRepDailyRead],
    summary="Top N vendedores por revenue, órdenes o productos en un rango",
)
def get_top_sales_reps(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    order_by: str = Query(default="revenue", pattern="^(revenue|orders|products)$"),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    start_date = start_date.date()
    end_date = end_date.date()

    sort_col = {
        "revenue": func.sum(AnalyticsSalesRepDaily.revenue_generated),
        "orders": func.sum(AnalyticsSalesRepDaily.total_orders),
        "products": func.sum(AnalyticsSalesRepDaily.total_products_sold),
    }[order_by]

    stmt = (
        select(
            AnalyticsSalesRepDaily.sales_rep_id,
            func.sum(AnalyticsSalesRepDaily.total_orders).label("total_orders"),
            func.sum(AnalyticsSalesRepDaily.total_clients).label("total_clients"),
            func.sum(AnalyticsSalesRepDaily.total_products_sold).label("total_products_sold"),
            func.sum(AnalyticsSalesRepDaily.revenue_generated).label("revenue_generated"),
            func.sum(AnalyticsSalesRepDaily.cost_generated).label("cost_generated"),
            func.sum(AnalyticsSalesRepDaily.margin_generated).label("margin_generated"),
            func.max(AnalyticsSalesRepDaily.date).label("date"),
            func.max(AnalyticsSalesRepDaily.id).label("id"),
            func.max(AnalyticsSalesRepDaily.created_at).label("created_at"),
        )
        .where(AnalyticsSalesRepDaily.date >= start_date)
        .where(AnalyticsSalesRepDaily.date <= end_date)
        .group_by(AnalyticsSalesRepDaily.sales_rep_id)
        .order_by(sort_col.desc())
        .limit(limit)
    )

    rows = db.execute(stmt).mappings().all()
    return [AnalyticsSalesRepDailyRead.model_validate(dict(r)) for r in rows]

@router.get(
    "/scheduler/jobs",
    summary="Lista los jobs programados y su próxima ejecución",
)
def list_scheduled_jobs(
    _: SalesRep = Depends(get_current_active_user),
):
    return [
        {
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time,
        }
        for job in scheduler.get_jobs()
    ]

@router.post(
    "/aggregate",
    summary="Ejecuta las agregaciones diarias para una fecha",
)
def run_aggregations(
    target_date: date = Query(...),
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    RunDailyAggregationsJob().run(target_date=target_date)
    return {
        "success": True,
        "target_date": target_date,
    }