"use client";

import Link from "next/link";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCategories } from "@/features/admin/categories/hooks/use-categories";

type ProductCategorySelectProps = {
  value: number | null | undefined;
  onChange: (categoryId: number | null) => void;
};

/**
 * Selector de categoría para el alta/edición de productos. Las categorías son
 * de cada distribuidora (se crean en Categorías); una privada deja el producto
 * solo para venta B2B interna.
 */
export function ProductCategorySelect({ value, onChange }: ProductCategorySelectProps) {
  const { data, isLoading } = useCategories();
  const categories = data?.items ?? [];

  if (!isLoading && categories.length === 0) {
    return (
      <p className="rounded-xl border border-dashed p-3 text-sm text-muted-foreground">
        Todavía no tenés categorías.{" "}
        <Link href="/admin/categories" className="font-semibold text-brand hover:underline">
          Creá la primera
        </Link>{" "}
        para poder asignarla.
      </p>
    );
  }

  return (
    <Select
      value={value ? String(value) : ""}
      onValueChange={(next) => onChange(next ? Number(next) : null)}
      disabled={isLoading}
    >
      <SelectTrigger className="w-full">
        <SelectValue placeholder={isLoading ? "Cargando..." : "Elegí una categoría"} />
      </SelectTrigger>
      <SelectContent>
        {categories.map((category) => (
          <SelectItem key={category.id} value={String(category.id)}>
            {category.name}
            {!category.is_public ? " (privada)" : ""}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
