from __future__ import annotations
from datetime import date
from decimal import Decimal
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.analytics.repositories.analytics_client_daily_repository import (
    AnalyticsClientDailyRepository,
)
from app.analytics.schemas.analytics_client_daily_schema import (
    AnalyticsClientDailyCreate,
    AnalyticsClientDailyRead,
)
from app.models.product_model import Product
from app.models.sales_invoice_model import SalesInvoice
from app.models.sales_invoice_item_model import SalesInvoiceItem

class AnalyticsClientDailyService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AnalyticsClientDailyRepository()

    def get_daily_metrics(
        self,
        *,
        target_date: date,
    ) -> list[AnalyticsClientDailyRead]:
        """
        Todos los clientes con métricas para una fecha dada.
        Usado por GET /analytics/clients/daily
        """
        items = self.repo.list_by_date(self.db, target_date)
        return [AnalyticsClientDailyRead.model_validate(i) for i in items]

    def get_client_metrics(
        self,
        *,
        client_id: int,
        target_date: date,
    ) -> AnalyticsClientDailyRead | None:
        """
        Métricas de un cliente específico para una fecha.
        Usado por GET /analytics/clients/daily/{client_id}
        """
        item = self.repo.get_by_date_and_client(self.db, target_date, client_id)
        if not item:
            return None
        return AnalyticsClientDailyRead.model_validate(item)

    def get_client_history(
        self,
        *,
        client_id: int,
        start_date: date,
        end_date: date,
        limit: int = 90,
    ) -> list[AnalyticsClientDailyRead]:
        """
        Histórico de un cliente en un rango de fechas.
        Usado por GET /analytics/clients/{client_id}/history
        """
        data = self.repo.list_by_client(
            self.db,
            client_id=client_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        return [AnalyticsClientDailyRead.model_validate(d) for d in data]

    def compute_client_metrics(
        self,
        db: Session,
        *,
        target_date: date,
    ) -> list[AnalyticsClientDailyCreate]:
        """
        Calcula las métricas de clientes para una fecha dada a partir de sales_invoices.

        Pasos:
        1. Agrega totales por client_id (órdenes, revenue, cost, margin).
        2. Para cada client_id, construye el JSONB products_bought con
           [{product_id, qty, amount}] y el conteo unique_products_count.

        Solo remitos con status == 'confirmed' y client_id no nulo. Un
        remito en 'draft' todavía puede editarse o cancelarse, y como este
        job corre una vez por día y graba un snapshot fijo por fecha, un
        remito que se confirma o cancela después de que corrió el job para
        su invoice_date jamás se recalcularía si contáramos los drafts acá.
        (Nota: 'client_id no nulo' ya no excluye ventas ONLINE — los
        pedidos de la tienda siempre tienen client_id asociado al cliente
        logueado.)
        """
        totals_stmt = (
            select(
                SalesInvoice.client_id,
                func.count(func.distinct(SalesInvoice.id)),
                func.coalesce(func.sum(SalesInvoice.total_amount), 0),
                func.coalesce(func.sum(SalesInvoice.total_cost), 0),
                func.coalesce(func.sum(SalesInvoice.margin_amount), 0),
            )
            .where(SalesInvoice.invoice_date == target_date)
            .where(SalesInvoice.status == "confirmed")
            .where(SalesInvoice.client_id.is_not(None))
            .group_by(SalesInvoice.client_id)
        )

        totals_rows = db.execute(totals_stmt).all()

        if not totals_rows:
            return []

        client_ids = [row[0] for row in totals_rows]

        products_stmt = (
            select(
                SalesInvoice.client_id,
                SalesInvoiceItem.product_id,
                func.coalesce(func.sum(SalesInvoiceItem.quantity), 0),
                func.coalesce(func.sum(SalesInvoiceItem.subtotal), 0),
            )
            .join(
                SalesInvoice,
                SalesInvoice.id == SalesInvoiceItem.sales_invoice_id,
            )
            .where(SalesInvoice.invoice_date == target_date)
            .where(SalesInvoice.status == "confirmed")
            .where(SalesInvoice.client_id.in_(client_ids))
            .where(SalesInvoiceItem.product_id.is_not(None))
            .group_by(
                SalesInvoice.client_id,
                SalesInvoiceItem.product_id,
            )
        )

        products_rows = db.execute(products_stmt).all()

        # Fetch product metadata (name, category, brand) for all involved product_ids
        all_product_ids = list({row[1] for row in products_rows})
        product_meta: dict[int, dict[str, str | None]] = {}
        if all_product_ids:
            meta_rows = db.execute(
                select(Product.id, Product.name, Product.category, Product.brand)
                .where(Product.id.in_(all_product_ids))
            ).all()
            for pid, pname, pcat, pbrand in meta_rows:
                product_meta[pid] = {
                    "product_name": pname,
                    "category": pcat,
                    "brand": pbrand,
                }

        products_by_client: dict[int, list[dict[str, Any]]] = {}
        for client_id, product_id, qty, amount in products_rows:
            meta = product_meta.get(product_id, {})
            products_by_client.setdefault(client_id, []).append(
                {
                    "product_id": product_id,
                    "qty": int(qty),
                    "amount": str(amount),
                    "product_name": meta.get("product_name"),
                    "category": meta.get("category"),
                    "brand": meta.get("brand"),
                }
            )

        results: list[AnalyticsClientDailyCreate] = []

        for (
            client_id,
            total_orders,
            revenue,
            cost,
            margin,
        ) in totals_rows:
            bought = products_by_client.get(client_id, [])
            categories_summary = _compute_categories_summary(bought)

            results.append(
                AnalyticsClientDailyCreate(
                    date=target_date,
                    client_id=client_id,
                    total_orders=int(total_orders),
                    revenue_generated=Decimal(str(revenue)),
                    cost_generated=Decimal(str(cost)),
                    margin_generated=Decimal(str(margin)),
                    products_bought=bought,
                    unique_products_count=len(bought),
                    categories_summary=categories_summary,
                )
            )

        return results

    def save_daily_snapshots(
        self,
        db: Session,
        *,
        metrics: list[AnalyticsClientDailyCreate],
    ) -> list[AnalyticsClientDailyRead]:
        results = []

        for item in metrics:
            item = self._normalize(item)
            item = self._compute_metrics(item)
            obj = self.repo.upsert(db, item)
            results.append(AnalyticsClientDailyRead.model_validate(obj))

        return results

    def delete(
        self,
        db: Session,
        *,
        target_date: date,
        client_id: int,
    ) -> None:
        self.repo.delete(db, target_date, client_id)

    def _normalize(
        self,
        data: AnalyticsClientDailyCreate,
    ) -> AnalyticsClientDailyCreate:
        data.total_orders = max(0, data.total_orders)
        data.unique_products_count = max(0, data.unique_products_count)

        return data

    def _compute_metrics(
        self,
        data: AnalyticsClientDailyCreate,
    ) -> AnalyticsClientDailyCreate:
        if data.margin_generated == 0:
            data.margin_generated = (
                data.revenue_generated - data.cost_generated
            )

        if data.revenue_generated < 0:
            data.revenue_generated = Decimal("0")

        if data.cost_generated < 0:
            data.cost_generated = Decimal("0")

        if data.unique_products_count == 0 and data.products_bought:
            data.unique_products_count = len(data.products_bought)

        return data
    def aggregate_date(
        self,
        db: Session,
        *,
        target_date: date,
    ) -> list[AnalyticsClientDailyRead]:
        """
        Método de conveniencia que computa y persiste las métricas de clientes
        para una fecha. Llamado por ClientDailyJob.
        """
        metrics = self.compute_client_metrics(db, target_date=target_date)
        return self.save_daily_snapshots(db, metrics=metrics)

def _compute_categories_summary(
    products_bought: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Agrupa los productos comprados por categoría y devuelve un resumen
    con qty total, amount total y cantidad de productos únicos por categoría.
    """
    summary: dict[str, dict[str, Any]] = {}

    for item in products_bought:
        cat = item.get("category") or "Sin categoría"
        qty = int(item.get("qty", 0))
        amount = Decimal(str(item.get("amount", "0")))

        if cat not in summary:
            summary[cat] = {"category": cat, "qty": 0, "amount": Decimal("0"), "unique_products": 0}

        summary[cat]["qty"] += qty
        summary[cat]["amount"] += amount
        summary[cat]["unique_products"] += 1

    return [
        {
            "category": v["category"],
            "qty": v["qty"],
            "amount": str(v["amount"]),
            "unique_products": v["unique_products"],
        }
        for v in sorted(summary.values(), key=lambda x: x["amount"], reverse=True)
    ]