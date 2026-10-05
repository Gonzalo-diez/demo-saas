"""
Precio de venta a partir del costo y un % de remarque.

    costo 200 + remarque 40%  ->  280
    costo 286,07 + 40%        ->  400,50  ->  se redondea a  401   (400,49 -> 400)

El precio de venta SIEMPRE se redondea al peso entero (mitad hacia arriba): nada de
centavos en las listas de precios.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

_CENTS = Decimal("0.01")
_ONE = Decimal("1")


def _to_decimal(value) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def round_sale_price(value) -> Decimal:
    """Redondea al entero más cercano (400,50 -> 401 · 400,49 -> 400) y lo devuelve con 2 decimales."""
    rounded = _to_decimal(value).quantize(_ONE, rounding=ROUND_HALF_UP)
    return rounded.quantize(_CENTS)


def price_from_markup(unit_cost, markup_percent) -> Decimal:
    """Precio de venta = costo + remarque %, redondeado al peso entero."""
    cost = _to_decimal(unit_cost)
    markup = _to_decimal(markup_percent)
    return round_sale_price(cost * (Decimal("100") + markup) / Decimal("100"))
