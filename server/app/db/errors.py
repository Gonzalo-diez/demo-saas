from sqlalchemy.exc import IntegrityError

def handle_product_integrity_error(db, exc: IntegrityError) -> None:
    db.rollback()
    message = str(exc.orig).lower()

    if "products_slug_key" in message or "slug" in message:
        raise ValueError("Ya existe un producto con este slug.")
    if "products_sku_key" in message or "sku" in message:
        raise ValueError("Hay un producto con este SKU.")
    if "ck_products_price_non_negative" in message:
        raise ValueError("El precio no puede ser negativo.")
    if "ck_products_stock_non_negative" in message:
        raise ValueError("El stock no puede ser negativo.")

    raise ValueError("No se pudo guardar el producto por una restricción de integridad.")