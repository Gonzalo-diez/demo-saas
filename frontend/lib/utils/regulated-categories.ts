import { resolveCategory } from "@/lib/utils/category-normalizer";

export const REGULATED_CATEGORY_VALUES = new Set([
  "cigarrillos eco",
  "masalin bat",
  "tabaco accesorios",
]);
 
export function isRegulatedCategory(category: string | null | undefined): boolean {
  const resolved = resolveCategory(category);
  if (!resolved) return false;
  return REGULATED_CATEGORY_VALUES.has(resolved.value);
}
 
export function cartHasRegulatedItems(
  items: { category?: string | null }[],
): boolean {
  return items.some((item) => isRegulatedCategory(item.category));
}