"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useProductCategories } from "@/features/admin/products/hooks/use-product-categories";
import {
  findCatalogCategory,
  isUnclassifiedCategory,
  normalizeCategoryKey,
} from "@/features/admin/products/utils/category-utils";
import { categories as catalogCategories } from "@/types/categories";

const NEW_CATEGORY = "__new__";
const UNCLASSIFIED = "__unclassified__";
const MAX_CATEGORY_LENGTH = 100;

type ProductCategorySelectProps = {
  value: string | null | undefined;
  onChange: (value: string | null) => void;
};

/**
 * Selector de categoría para el alta/edición manual de productos:
 *  - Catálogo online: categorías seteadas (se ven en /catalogo, exigen imagen).
 *  - Solo B2B: categorías libres ya existentes (no salen en el catálogo).
 *  - Crear categoría nueva: siempre libre (solo B2B).
 */
export function ProductCategorySelect({
  value,
  onChange,
}: ProductCategorySelectProps) {
  const { data, isLoading } = useProductCategories();
  const aliases = data?.catalog_aliases ?? {};
  const freeCategories = data?.free ?? [];

  const [creating, setCreating] = useState(false);
  const [draft, setDraft] = useState("");

  const currentValue = value?.trim() ?? "";
  const unclassified = isUnclassifiedCategory(currentValue);
  const catalogMatch = findCatalogCategory(
    currentValue,
    catalogCategories,
    aliases,
  );

  // Lista de libres + la categoría actual si por algún motivo no está en la lista
  // (ej. todavía cargando), para que el Select siempre tenga un item que mostrar.
  const freeOptions = useMemo(() => {
    const options = [...freeCategories];
    if (
      currentValue &&
      !unclassified &&
      !catalogMatch &&
      !creating &&
      !options.some(
        (option) =>
          normalizeCategoryKey(option) === normalizeCategoryKey(currentValue),
      )
    ) {
      options.push(currentValue);
    }
    return options.sort((a, b) => a.localeCompare(b, "es"));
  }, [freeCategories, currentValue, unclassified, catalogMatch, creating]);

  const selectValue = creating
    ? NEW_CATEGORY
    : !currentValue
      ? ""
      : unclassified
        ? UNCLASSIFIED
        : catalogMatch
          ? catalogMatch.value
          : (freeOptions.find(
              (option) =>
                normalizeCategoryKey(option) ===
                normalizeCategoryKey(currentValue),
            ) ?? currentValue);

  // --- Validación del nombre de una categoría nueva ---
  const draftKey = normalizeCategoryKey(draft);
  const draftCatalogMatch = draftKey
    ? findCatalogCategory(draft, catalogCategories, aliases)
    : null;
  const draftExisting = draftKey
    ? freeCategories.find((option) => normalizeCategoryKey(option) === draftKey)
    : undefined;
  const draftIsUnclassified = isUnclassifiedCategory(draft);

  const handleSelect = (next: string) => {
    if (next === NEW_CATEGORY) {
      setCreating(true);
      setDraft("");
      onChange(null);
      return;
    }

    setCreating(false);
    setDraft("");
    onChange(next === UNCLASSIFIED ? currentValue : next);
  };

  const handleDraftChange = (text: string) => {
    setDraft(text);
    const key = normalizeCategoryKey(text);

    // Vacío, reservado o colisión con una de catálogo: no es un valor válido
    // hasta que la persona decida (ver avisos abajo).
    if (
      !key ||
      isUnclassifiedCategory(text) ||
      findCatalogCategory(text, catalogCategories, aliases)
    ) {
      onChange(null);
      return;
    }

    // Si ya existe una libre equivalente (mayúsculas/tildes), reusamos su grafía.
    const existing = freeCategories.find(
      (option) => normalizeCategoryKey(option) === key,
    );
    onChange(existing ?? text.trim().replace(/\s+/g, " ").slice(0, MAX_CATEGORY_LENGTH));
  };

  const pickCatalogCategory = (categoryValue: string) => {
    setCreating(false);
    setDraft("");
    onChange(categoryValue);
  };

  const isFree = !!currentValue && !unclassified && !catalogMatch;

  return (
    <div className="space-y-2">
      <Select
        value={selectValue}
        onValueChange={handleSelect}
        disabled={isLoading && !currentValue}
      >
        <SelectTrigger>
          <SelectValue
            placeholder={isLoading ? "Cargando categorías..." : "Seleccionar categoría"}
          />
        </SelectTrigger>

        <SelectContent>
          {unclassified && (
            <>
              <SelectItem value={UNCLASSIFIED}>Sin clasificar (pendiente)</SelectItem>
              <SelectSeparator />
            </>
          )}

          <SelectGroup>
            <SelectLabel>Catálogo online</SelectLabel>
            {catalogCategories.map((category) => (
              <SelectItem key={category.id} value={category.value}>
                {category.name}
              </SelectItem>
            ))}
          </SelectGroup>

          {freeOptions.length > 0 && (
            <>
              <SelectSeparator />
              <SelectGroup>
                <SelectLabel>Solo B2B (no se muestran online)</SelectLabel>
                {freeOptions.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectGroup>
            </>
          )}

          <SelectSeparator />
          <SelectItem value={NEW_CATEGORY}>+ Crear categoría nueva</SelectItem>
        </SelectContent>
      </Select>

      {creating && (
        <div className="space-y-2 rounded-xl border border-dashed p-3">
          <Input
            autoFocus
            value={draft}
            maxLength={MAX_CATEGORY_LENGTH}
            onChange={(event) => handleDraftChange(event.target.value)}
            placeholder="Nombre de la categoría nueva"
          />

          {draftIsUnclassified && (
            <p className="text-xs text-destructive">
              &quot;Sin clasificar&quot; es un estado reservado. Elegí otro nombre.
            </p>
          )}

          {draftCatalogMatch && (
            <div className="space-y-2 rounded-lg border border-amber-500/40 bg-amber-500/10 p-2.5 text-xs">
              <p>
                &quot;{draft.trim()}&quot; coincide con la categoría de catálogo{" "}
                <span className="font-medium">{draftCatalogMatch.name}</span>. Si
                la usás, el producto se muestra en la tienda online y necesita
                imagen. Para una categoría solo B2B, elegí otro nombre.
              </p>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => pickCatalogCategory(draftCatalogMatch.value)}
              >
                Usar {draftCatalogMatch.name}
              </Button>
            </div>
          )}

          {!draftCatalogMatch && !draftIsUnclassified && draftExisting && (
            <p className="text-xs text-muted-foreground">
              Ya existe &quot;{draftExisting}&quot;; se va a usar esa.
            </p>
          )}
        </div>
      )}

      {catalogMatch && (
        <p className="text-xs text-muted-foreground">
          Categoría de catálogo: se muestra en la tienda online y requiere
          imagen para activarse.
        </p>
      )}

      {(isFree || (creating && currentValue)) && (
        <p className="text-xs text-muted-foreground">
          Solo B2B: no aparece en el catálogo online y no requiere imagen.
        </p>
      )}

      {unclassified && (
        <p className="text-xs text-muted-foreground">
          Sin clasificar: el producto queda inactivo hasta que le asignes una
          categoría.
        </p>
      )}
    </div>
  );
}
