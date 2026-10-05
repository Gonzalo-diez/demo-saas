ALLOWED_SORT_FIELDS = {
    "name-asc",
    "name-desc",
    "price-asc",
    "price-desc",
}

ALLOWED_PRODUCT_STATUSES = {"ACTIVE", "INACTIVE", "DRAFT"}

EXPECTED_COLUMNS = [
    "sku",
    "name",
    "description",
    "brand",
    "category",
    "unit_cost",
    "unit_price",
    "stock",
    "stock_min",
    "is_active",
]

REQUIRED_COLUMNS = [
    "sku",
    "name",
    "unit_cost",
    "unit_price",
    "stock",
]

TRUE_VALUES = {"true", "1", "si", "sí", "yes", "y", "activo", "active"}
FALSE_VALUES = {"false", "0", "no", "n", "inactivo", "inactive"}