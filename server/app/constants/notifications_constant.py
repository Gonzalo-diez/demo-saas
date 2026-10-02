NOTIFICATION_CATEGORIES = {"stock", "check"}

# type -> (categoría, severidad, nivel de urgencia)
#
# "severidad" es solo para que el frontend pinte el aviso (info/warning/critical).
# "nivel" ordena la urgencia de los estados posibles de UNA misma entidad
# (un producto o un cheque): si el nivel sube (ej. stock bajo -> sin stock) el
# aviso se vuelve a marcar como no leído; si baja (ej. se repuso stock) solo se
# actualiza el texto, sin volver a avisar.
NOTIFICATION_TYPE_META: dict[str, tuple[str, str, int]] = {
    # Stock
    "stock_near_min": ("stock", "info", 1),
    "stock_low": ("stock", "warning", 2),
    "stock_out": ("stock", "critical", 3),
    # Cheques (pendientes de depositar/acreditar)
    "check_upcoming": ("check", "info", 1),
    "check_payable": ("check", "warning", 2),
    "check_due_soon": ("check", "warning", 3),
    "check_overdue": ("check", "critical", 4),
    # Evento puntual (no es una condición que se "resuelve sola")
    "check_rejected": ("check", "critical", 5),
}

ALLOWED_NOTIFICATION_TYPES = set(NOTIFICATION_TYPE_META.keys())

# Notificaciones que registran algo que pasó una vez, en vez de una condición
# vigente: no se resuelven solas, se archivan con el tiempo.
EVENT_NOTIFICATION_TYPES = {"check_rejected"}

ENTITY_TYPE_PRODUCT = "product"
ENTITY_TYPE_CHECK = "check"
