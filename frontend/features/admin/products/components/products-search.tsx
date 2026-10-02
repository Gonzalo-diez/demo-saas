"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { ProductSort, ProductStatusFilter } from "@/features/admin/products/types";

type ProductsSearchProps = {
  value: string;
  onChange: (value: string) => void;
  status: ProductStatusFilter;
  onStatusChange: (value: ProductStatusFilter) => void;
  brand: string;
  onBrandChange: (value: string) => void;
  sort: ProductSort;
  onSortChange: (value: ProductSort) => void;
};

export function ProductsSearch({
  value,
  onChange,
  status,
  onStatusChange,
  brand,
  onBrandChange,
  sort,
  onSortChange,
}: ProductsSearchProps) {
  return (
    <div className="rounded-xl border bg-background p-4 shadow-sm">
      <div className="space-y-1">
        <h3 className="text-sm font-semibold">Buscar productos</h3>
        <p className="text-xs text-muted-foreground">
          Buscá, filtrá y ordená productos del catálogo.
        </p>
      </div>

      <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <Input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Nombre, SKU, marca o categoría"
          className="xl:col-span-2"
        />

        <Select
          value={status}
          onValueChange={(value) => onStatusChange(value as ProductStatusFilter)}
        >
          <SelectTrigger>
            <SelectValue placeholder="Estado" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos</SelectItem>
            <SelectItem value="active">Activos</SelectItem>
            <SelectItem value="inactive">Inactivos</SelectItem>
          </SelectContent>
        </Select>

        <Input
          value={brand}
          onChange={(e) => onBrandChange(e.target.value)}
          placeholder="Filtrar por marca"
        />

        <Select
          value={sort || "__default__"}
          onValueChange={(value) =>
            onSortChange(value === "__default__" ? "" : (value as ProductSort))
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="Orden por defecto" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__default__">Orden por defecto</SelectItem>
            <SelectItem value="name-asc">Nombre A → Z</SelectItem>
            <SelectItem value="name-desc">Nombre Z → A</SelectItem>
            <SelectItem value="price-asc">Precio menor → mayor</SelectItem>
            <SelectItem value="price-desc">Precio mayor → menor</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="mt-3">
        <Button
          type="button"
          variant="outline"
          onClick={() => {
            onChange("");
            onStatusChange("all");
            onBrandChange("");
            onSortChange("");
          }}
        >
          Limpiar filtros
        </Button>
      </div>
    </div>
  );
}