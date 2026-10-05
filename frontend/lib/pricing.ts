/**
 * Precio de venta a partir del costo y un % de remarque. Espeja app/utils/pricing.py del
 * backend (que es el que manda): el precio SIEMPRE se redondea al peso entero.
 *
 *   costo 200 + 40%  -> 280
 *   400,50 -> 401  ·  400,49 -> 400
 */

/** Redondea al entero más cercano; la mitad sube (400,50 -> 401). */
export function roundSalePrice(value: number): number {
  if (!Number.isFinite(value)) return 0;
  // toFixed(6) saca el ruido de coma flotante (280.00000000000006) antes de redondear.
  return Math.floor(Number(value.toFixed(6)) + 0.5);
}

/** Costo + remarque %, redondeado al peso entero. */
export function priceFromMarkup(unitCost: number, markupPercent: number): number {
  if (!Number.isFinite(unitCost) || !Number.isFinite(markupPercent)) return 0;
  return roundSalePrice((unitCost * (100 + markupPercent)) / 100);
}
