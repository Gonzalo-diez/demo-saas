from collections.abc import Callable
from typing import Any
from sqlalchemy.orm import Session
from app.ai.tools.catalog_tool import (
    get_inactive_products_tool,
    get_low_stock_products_tool,
    get_product_catalog_overview_tool,
    get_products_by_category_tool,
    search_products_tool,
)
from app.ai.tools.client_tool import (
    get_client_overview_tool,
    get_branches_without_orders_tool,
    get_client_overview_tool,
    get_clients_by_sales_rep_tool,
    get_clients_with_coordinates_tool,
    get_clients_without_orders_tool,
    get_clients_without_sales_rep_tool,
    get_recent_clients_tool,
)
from app.ai.tools.dashboard_tool import get_dashboard_summary_tool
from app.ai.tools.order_tool import (
    get_order_overview_tool,
    get_orders_by_sales_rep_tool,
    get_orders_by_status_tool,
    get_pending_orders_tool,
    get_recent_orders_tool,
)
from app.ai.tools.sales_tool import (
    get_sales_rep_client_counts_tool,
    get_sales_rep_order_counts_tool,
    get_sales_rep_performance_tool,
    get_sales_reps_tool,
    get_sales_team_overview_tool,
)
from app.ai.tools.supplier_tool import (
    get_suppliers_tool,
    get_supplier_overview_tool,
)

from app.ai.tools.sales_invoice_tool import (
    get_recent_sales_invoices_tool,
    get_sales_invoice_overview_tool,
)

from app.ai.tools.purchase_invoice_tool import (
    get_recent_purchase_invoices_tool,
    get_purchase_invoice_overview_tool,
)

from app.ai.tools.inventory_movements_tool import (
    get_recent_inventory_movements_tool,
    get_inventory_movement_overview_tool,
)
from app.ai.tools.analytics_tool import (
    get_daily_summary_tool,
    get_top_products_tool,
    get_top_sales_reps_tool,
    get_product_trend_tool,
    get_zone_sales_tool,
    get_period_summary_tool,
    get_top_clients_tool,
    get_client_trend_tool,
)

ToolFn = Callable[..., dict | list | str | int | float | None]

VALID_ORDER_STATUSES = {
    "pending",
    "confirmed",
    "completed",
    "cancelled",
}

TOOLS_REGISTRY: dict[str, dict[str, Any]] = {
    "get_dashboard_summary": {
        "fn": get_dashboard_summary_tool,
        "description": "Devuelve un resumen general del negocio con totales principales.",
        "params_schema": {},
    },
    "get_low_stock_products": {
        "fn": get_low_stock_products_tool,
        "description": "Devuelve productos activos con stock actual menor o igual al stock mínimo.",
        "params_schema": {
            "limit": {"type": "int", "required": False, "default": 10, "min": 1, "max": 100},
        },
    },
    "get_inactive_products": {
        "fn": get_inactive_products_tool,
        "description": "Devuelve productos inactivos.",
        "params_schema": {
            "limit": {"type": "int", "required": False, "default": 10, "min": 1, "max": 100},
        },
    },
    "search_products": {
        "fn": search_products_tool,
        "description": "Busca productos por nombre, sku, marca o categoría.",
        "params_schema": {
            "query": {"type": "str", "required": True, "min_length": 1, "max_length": 120},
            "limit": {"type": "int", "required": False, "default": 10, "min": 1, "max": 100},
        },
    },
    "get_products_by_category": {
        "fn": get_products_by_category_tool,
        "description": "Devuelve productos filtrados por categoría.",
        "params_schema": {
            "category": {"type": "str", "required": True, "min_length": 1, "max_length": 120},
            "limit": {"type": "int", "required": False, "default": 20, "min": 1, "max": 100},
        },
    },
    "get_product_catalog_overview": {
        "fn": get_product_catalog_overview_tool,
        "description": "Devuelve métricas generales del catálogo de productos.",
        "params_schema": {},
    },
    "get_recent_clients": {
        "fn": get_recent_clients_tool,
        "description": "Devuelve los clientes más recientes.",
        "params_schema": {
            "limit": {"type": "int", "required": False, "default": 10, "min": 1, "max": 100},
        },
    },
    "get_clients_without_sales_rep": {
        "fn": get_clients_without_sales_rep_tool,
        "description": "Devuelve clientes sin vendedor asignado.",
        "params_schema": {
            "limit": {"type": "int", "required": False, "default": 20, "min": 1, "max": 100},
        },
    },
    "get_clients_by_sales_rep": {
        "fn": get_clients_by_sales_rep_tool,
        "description": "Devuelve clientes asignados a un vendedor.",
        "params_schema": {
            "sales_rep_id": {"type": "int", "required": True, "min": 1},
            "limit": {"type": "int", "required": False, "default": 20, "min": 1, "max": 100},
        },
    },
    "get_clients_with_coordinates": {
        "fn": get_clients_with_coordinates_tool,
        "description": "Devuelve clientes con coordenadas disponibles.",
        "params_schema": {
            "limit": {"type": "int", "required": False, "default": 20, "min": 1, "max": 100},
        },
    },
    "get_clients_without_orders": {
        "fn": get_clients_without_orders_tool,
        "description": "Devuelve clientes que todavía no tienen órdenes.",
        "params_schema": {
            "limit": {"type": "int", "required": False, "default": 20, "min": 1, "max": 100},
        },
    },
    "get_client_overview": {
        "fn": get_client_overview_tool,
        "description": "Devuelve métricas generales de clientes.",
        "params_schema": {},
    },
    "get_branches_without_orders": {
        "fn": get_branches_without_orders_tool,
        "description": "Devuelve sucursales activas que todavía no tienen órdenes.",
        "params_schema": {
            "limit": {"type": "int", "required": False, "default": 20, "min": 1, "max": 100},
        },
    },
    "get_recent_orders": {
        "fn": get_recent_orders_tool,
        "description": "Devuelve las órdenes más recientes.",
        "params_schema": {
            "limit": {"type": "int", "required": False, "default": 10, "min": 1, "max": 100},
        },
    },
    "get_pending_orders": {
        "fn": get_pending_orders_tool,
        "description": "Devuelve órdenes pendientes.",
        "params_schema": {
            "limit": {"type": "int", "required": False, "default": 10, "min": 1, "max": 100},
        },
    },
    "get_orders_by_status": {
        "fn": get_orders_by_status_tool,
        "description": "Devuelve órdenes filtradas por estado.",
        "params_schema": {
            "status": {
                "type": "str",
                "required": True,
                "allowed": sorted(VALID_ORDER_STATUSES),
            },
            "limit": {"type": "int", "required": False, "default": 20, "min": 1, "max": 100},
        },
    },
    "get_orders_by_sales_rep": {
        "fn": get_orders_by_sales_rep_tool,
        "description": "Devuelve órdenes de un vendedor específico.",
        "params_schema": {
            "sales_rep_id": {"type": "int", "required": True, "min": 1},
            "limit": {"type": "int", "required": False, "default": 20, "min": 1, "max": 100},
        },
    },
    "get_order_overview": {
        "fn": get_order_overview_tool,
        "description": "Devuelve métricas generales de órdenes.",
        "params_schema": {},
    },
    "get_sales_reps": {
        "fn": get_sales_reps_tool,
        "description": "Devuelve la lista de vendedores.",
        "params_schema": {
            "limit": {"type": "int", "required": False, "default": 20, "min": 1, "max": 100},
        },
    },
    "get_sales_rep_client_counts": {
        "fn": get_sales_rep_client_counts_tool,
        "description": "Devuelve cantidad de clientes por vendedor.",
        "params_schema": {},
    },
    "get_sales_rep_order_counts": {
        "fn": get_sales_rep_order_counts_tool,
        "description": "Devuelve cantidad de órdenes por vendedor.",
        "params_schema": {},
    },
        "get_suppliers": {
            "fn": get_suppliers_tool,
            "description": "Lista de proveedores.",
            "params_schema": {
                "limit": {"type": "int", "required": False, "default": 20}
            },
    },
    "get_supplier_overview": {
        "fn": get_supplier_overview_tool,
        "description": "Resumen de proveedores.",
        "params_schema": {},
    },
    "get_recent_sales_invoices": {
        "fn": get_recent_sales_invoices_tool,
        "description": "Remitos de venta recientes.",
        "params_schema": {},
    },
    "get_sales_invoice_overview": {
        "fn": get_sales_invoice_overview_tool,
        "description": "Resumen de facturación de ventas.",
        "params_schema": {},
    },
    "get_recent_purchase_invoices": {
        "fn": get_recent_purchase_invoices_tool,
        "description": "Remitos de compra recientes.",
        "params_schema": {},
    },
    "get_purchase_invoice_overview": {
        "fn": get_purchase_invoice_overview_tool,
        "description": "Resumen de compras.",
        "params_schema": {},
    },
    "get_recent_inventory_movements": {
        "fn": get_recent_inventory_movements_tool,
        "description": "Movimientos de inventario recientes.",
        "params_schema": {},
    },
    "get_inventory_movement_overview": {
        "fn": get_inventory_movement_overview_tool,
        "description": "Resumen de movimientos de inventario.",
        "params_schema": {},
    },
    "get_sales_rep_performance": {
        "fn": get_sales_rep_performance_tool,
        "description": "Devuelve desempeño comercial por vendedor.",
        "params_schema": {},
    },
    "get_sales_team_overview": {
        "fn": get_sales_team_overview_tool,
        "description": "Devuelve métricas generales del equipo de ventas.",
        "params_schema": {},
    },
    "get_daily_summary": {
        "fn": get_daily_summary_tool,
        "description": "Resumen global del negocio para una fecha específica: órdenes, clientes, revenue, margen y ticket promedio.",
        "params_schema": {
            "target_date": {"type": "str", "required": False, "default": None},
        },
    },
    "get_top_products": {
        "fn": get_top_products_tool,
        "description": "Ranking de productos más vendidos por revenue en un rango de fechas. Devuelve cantidad, revenue, costo, margen y porcentaje de margen por producto.",
        "params_schema": {
            "start_date": {"type": "str", "required": False, "default": None},
            "end_date":   {"type": "str", "required": False, "default": None},
            "limit":      {"type": "int", "required": False, "default": 10, "min": 1, "max": 50},
        },
    },
    "get_top_sales_reps": {
        "fn": get_top_sales_reps_tool,
        "description": "Ranking de vendedores por revenue generado en un rango de fechas. Incluye órdenes, clientes, revenue, margen y porcentaje de margen.",
        "params_schema": {
            "start_date": {"type": "str", "required": False, "default": None},
            "end_date":   {"type": "str", "required": False, "default": None},
            "limit":      {"type": "int", "required": False, "default": 10, "min": 1, "max": 50},
        },
    },
    "get_product_trend": {
        "fn": get_product_trend_tool,
        "description": "Evolución diaria de ventas de un producto específico en un rango de fechas: cantidad, revenue, costo y margen día a día.",
        "params_schema": {
            "product_id": {"type": "int", "required": True, "min": 1},
            "start_date": {"type": "str", "required": False, "default": None},
            "end_date":   {"type": "str", "required": False, "default": None},
        },
    },
    "get_zone_sales": {
        "fn": get_zone_sales_tool,
        "description": "Ranking de zonas geográficas (H3) por revenue en un rango de fechas. Útil para analizar cobertura territorial y detectar zonas de alto/bajo desempeño.",
        "params_schema": {
            "start_date": {"type": "str", "required": False, "default": None},
            "end_date":   {"type": "str", "required": False, "default": None},
            "limit":      {"type": "int", "required": False, "default": 20, "min": 1, "max": 50},
        },
    },
    "get_period_summary": {
        "fn": get_period_summary_tool,
        "description": "Resumen acumulado del negocio para un rango de fechas: total de órdenes, clientes, revenue, margen y ticket promedio del período.",
        "params_schema": {
            "start_date": {"type": "str", "required": False, "default": None},
            "end_date":   {"type": "str", "required": False, "default": None},
        },
    },
    "get_top_clients": {
        "fn": get_top_clients_tool,
        "description": "Ranking de clientes por revenue generado en un rango de fechas. Incluye órdenes, revenue, costo, margen y porcentaje de margen por cliente.",
        "params_schema": {
            "start_date": {"type": "str", "required": False, "default": None},
            "end_date":   {"type": "str", "required": False, "default": None},
            "limit":      {"type": "int", "required": False, "default": 10, "min": 1, "max": 50},
        },
    },
    "get_client_trend": {
        "fn": get_client_trend_tool,
        "description": "Evolución diaria de métricas de un cliente específico en un rango de fechas: órdenes, revenue, margen y productos comprados día a día.",
        "params_schema": {
            "client_id":  {"type": "int", "required": True, "min": 1},
            "start_date": {"type": "str", "required": False, "default": None},
            "end_date":   {"type": "str", "required": False, "default": None},
        },
    },
}

def list_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "description": config["description"],
            "params_schema": config["params_schema"],
        }
        for name, config in TOOLS_REGISTRY.items()
    ]

def get_tool(name: str) -> dict[str, Any]:
    tool = TOOLS_REGISTRY.get(name)
    if tool is None:
        raise KeyError(name)
    return tool

def _cast_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise TypeError(f"'{field_name}' no puede ser boolean.")
    try:
        return int(value)
    except (TypeError, ValueError):
        raise TypeError(f"'{field_name}' debe ser un entero válido.")

def _cast_str(value: Any, field_name: str) -> str:
    if value is None:
        raise TypeError(f"'{field_name}' no puede ser null.")
    text = str(value).strip()
    if not text:
        raise ValueError(f"'{field_name}' no puede estar vacío.")
    return text

def _validate_field(field_name: str, value: Any, rules: dict[str, Any]) -> Any:
    field_type = rules.get("type")

    if field_type == "int":
        value = _cast_int(value, field_name)

        min_value = rules.get("min")
        max_value = rules.get("max")

        if min_value is not None and value < min_value:
            raise ValueError(f"'{field_name}' debe ser >= {min_value}.")
        if max_value is not None and value > max_value:
            raise ValueError(f"'{field_name}' debe ser <= {max_value}.")

        return value

    if field_type == "str":
        value = _cast_str(value, field_name)

        min_length = rules.get("min_length")
        max_length = rules.get("max_length")
        allowed = rules.get("allowed")

        if min_length is not None and len(value) < min_length:
            raise ValueError(f"'{field_name}' debe tener al menos {min_length} caracteres.")
        if max_length is not None and len(value) > max_length:
            raise ValueError(f"'{field_name}' debe tener como máximo {max_length} caracteres.")
        if allowed is not None and value not in allowed:
            raise ValueError(
                f"'{field_name}' debe ser uno de estos valores: {', '.join(allowed)}."
            )

        return value

    return value

def validate_tool_params(tool_name: str, params: dict[str, Any] | None) -> dict[str, Any]:
    tool = get_tool(tool_name)
    schema = tool.get("params_schema", {})
    params = params or {}

    if not isinstance(params, dict):
        raise TypeError("Los parámetros de la tool deben ser un objeto JSON.")

    validated: dict[str, Any] = {}

    for field_name, rules in schema.items():
        required = rules.get("required", False)

        if field_name not in params or params[field_name] is None:
            if "default" in rules:
                validated[field_name] = rules["default"]
                continue
            if required:
                raise ValueError(f"Falta el parámetro requerido '{field_name}'.")
            continue

        validated[field_name] = _validate_field(field_name, params[field_name], rules)

    return validated

def detect_fallback_tool(question: str) -> str | None:
    q = question.lower().strip()

    if any(word in q for word in ["stock", "producto", "productos", "catálogo", "catalogo", "sku", "marca", "categoría", "categoria"]):
        return "get_product_catalog_overview"

    if any(word in q for word in ["cliente", "clientes", "coordenadas", "mapa", "zona"]):
        return "get_client_overview"
    
    if any(word in q for word in ["top clientes", "mejor cliente", "ranking cliente", "cliente más compró", "clientes histórico"]):
        return "get_top_clients"

    if any(word in q for word in ["orden", "órdenes", "ordenes", "pedido", "pedidos", "estado"]):
        return "get_order_overview"

    if any(word in q for word in ["vendedor", "vendedores", "sales rep", "desempeño", "desempeno", "ventas"]):
        return "get_sales_rep_performance"

    if any(word in q for word in ["dashboard", "resumen", "negocio", "empresa", "general"]):
        return "get_dashboard_summary"
    
    if any(word in q for word in ["sucursal", "sucursales", "ubicación", "ubicaciones", "mapa", "zona", "coordenadas"]):
        return "get_clients_with_coordinates"
    
    if any(word in q for word in ["sucursales sin pedidos", "sucursales sin órdenes", "sucursales sin ordenes"]):
        return "get_branches_without_orders"
    
    if any(word in q for word in ["top productos", "más vendido", "ranking producto", "mejor producto"]):
        return "get_top_products"

    if any(word in q for word in ["mejor vendedor", "top vendedor", "ranking vendedor", "desempeño histórico"]):
        return "get_top_sales_reps"

    if any(word in q for word in ["resumen del período", "resumen del mes", "acumulado", "métricas del período"]):
        return "get_period_summary"

    if any(word in q for word in ["tendencia", "evolución", "histórico producto"]):
        return "get_product_trend"

    if any(word in q for word in ["zona", "zonas", "territorial", "cobertura geográfica", "mapa ventas"]):
        return "get_zone_sales"

    return None

def execute_tool(name: str, db: Session, **kwargs):
    tool = get_tool(name)
    validated_kwargs = validate_tool_params(name, kwargs)
    fn = tool["fn"]
    return fn(db, **validated_kwargs)