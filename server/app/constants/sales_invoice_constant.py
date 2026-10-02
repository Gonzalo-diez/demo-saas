ALLOWED_SALES_INVOICE_STATUSES = {
    "draft",
    "confirmed",
    "cancelled",
}

VALID_SALES_INVOICE_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"confirmed", "cancelled"},
    "confirmed": {"cancelled"},
    "cancelled": set(),
}