ALLOWED_ORDER_STATUSES = {
    "pending_confirmation",
    "confirmed",
    "preparing",
    "shipped",
    "delivered",
    "cancelled",
}

# Documento de venta que genera un pedido al pasar a 'preparing'.
ORDER_DOCUMENT_SALES_INVOICE = "sales_invoice"
ORDER_DOCUMENT_SALES_QUOTE = "sales_quote"

ALLOWED_ORDER_DOCUMENT_TYPES = {
    ORDER_DOCUMENT_SALES_INVOICE,
    ORDER_DOCUMENT_SALES_QUOTE,
}

ALLOWED_DELIVERY_TYPES = {
    "delivery",
    "pickup",
}

VALID_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "pending_confirmation": {"confirmed", "cancelled"},
    "confirmed": {"preparing", "cancelled"},
    "preparing": {"shipped", "cancelled"},
    "shipped": {"delivered"},
    "delivered": set(),
    "cancelled": set(),
}