from __future__ import annotations

import re
import unicodedata
from decimal import Decimal
from typing import Iterable


def normalize_text(value: str | None) -> str:
    """
    Normaliza un texto para comparaciones tolerantes a mayúsculas, tildes
    y espacios extra (nombres de producto, cliente, proveedor, etc.).
    """
    if not value:
        return ""

    text = str(value).strip().lower()
    text = "".join(
        char
        for char in unicodedata.normalize("NFD", text)
        if unicodedata.category(char) != "Mn"
    )
    text = re.sub(r"\s+", " ", text)
    return text


def item_key(product_id: int | None, product_sku: str | None, product_name: str | None) -> str:
    """
    Clave estable para identificar un producto dentro de un item importado,
    usando la señal más confiable disponible: id resuelto > SKU > nombre
    normalizado. Así dos documentos se pueden comparar aunque uno todavía
    no tenga el producto vinculado por id.
    """
    if product_id:
        return f"id:{product_id}"

    normalized_sku = normalize_text(product_sku)
    if normalized_sku:
        return f"sku:{normalized_sku}"

    return f"name:{normalize_text(product_name)}"


def build_items_signature(
    items: Iterable[dict],
) -> frozenset[tuple[str, int]]:
    """
    Arma la "firma" de un documento (remito/presupuesto) a partir de sus
    items, como un set de (clave_producto, cantidad). Dos documentos con
    la misma firma tienen exactamente los mismos productos y cantidades,
    sin importar el orden.

    Cada item debe ser un dict con keys: product_id, product_sku,
    product_name, quantity.
    """
    signature = set()

    for item in items:
        key = item_key(
            item.get("product_id"),
            item.get("product_sku"),
            item.get("product_name"),
        )
        quantity = item.get("quantity") or 0
        signature.add((key, int(quantity)))

    return frozenset(signature)


def is_same_document(
    candidate_signature: frozenset[tuple[str, int]],
    existing_signature: frozenset[tuple[str, int]],
) -> bool:
    """
    Match exacto: mismo set de (producto, cantidad). Documentos vacíos
    nunca se consideran duplicados entre sí.
    """
    return bool(candidate_signature) and candidate_signature == existing_signature


def row_signature(
    *,
    client_or_supplier_id: int,
    product_id: int | None,
    product_sku: str | None,
    product_name: str | None,
    quantity: int,
    unit_amount: Decimal | None,
) -> tuple:
    """
    Firma de una fila individual (usada para el import de cuenta corriente,
    donde no hay fecha por fila y hay que decidir fila por fila si ya fue
    importada antes). unit_amount se redondea a 2 decimales para tolerar
    pequeñas diferencias de representación numérica.
    """
    key = item_key(product_id, product_sku, product_name)
    rounded_amount = (
        Decimal(str(unit_amount)).quantize(Decimal("0.01"))
        if unit_amount is not None
        else None
    )
    return (client_or_supplier_id, key, int(quantity), rounded_amount)
