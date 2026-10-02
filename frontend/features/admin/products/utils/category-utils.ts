/**
 * Réplica de `_normalize_base` del backend (utils/category_normalizer.py):
 * minúsculas, sin tildes, "&" -> " y ", sin símbolos y espacios colapsados.
 * Se usa para comparar categorías (alias de catálogo, duplicados de libres).
 */
export function normalizeCategoryKey(value: string | null | undefined): string {
  if (!value) return "";

  return value
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/&/g, " y ")
    .replace(/[^a-z0-9\s-]/g, " ")
    .replace(/[-_]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export const UNCLASSIFIED_KEY = "sin clasificar";

export function isUnclassifiedCategory(value: string | null | undefined) {
  return normalizeCategoryKey(value) === UNCLASSIFIED_KEY;
}

type CatalogCategoryLike = { value: string; name: string };

/**
 * Devuelve la categoría de catálogo (de la lista estática `categories`) a la
 * que corresponde `value`, ya sea por valor/nombre exacto o por alias del
 * backend (ej. "Baterías" -> "pilas"). `null` si es una categoría libre.
 */
export function findCatalogCategory<T extends CatalogCategoryLike>(
  value: string | null | undefined,
  catalogCategories: readonly T[],
  aliases: Record<string, string>,
): T | null {
  const key = normalizeCategoryKey(value);
  if (!key || key === UNCLASSIFIED_KEY) return null;

  const canonical = aliases[key] ?? null;

  return (
    catalogCategories.find((category) => {
      const categoryKey = normalizeCategoryKey(category.value);
      const nameKey = normalizeCategoryKey(category.name);
      if (categoryKey === key || nameKey === key) return true;
      if (!canonical) return false;
      return (
        categoryKey === canonical || (aliases[categoryKey] ?? null) === canonical
      );
    }) ?? null
  );
}
