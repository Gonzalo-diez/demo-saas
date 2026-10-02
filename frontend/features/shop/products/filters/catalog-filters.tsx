"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useRef } from "react";
import { SearchFilter } from "@/features/shop/products/filters/search-filter";
import { BrandFilter } from "@/features/shop/products/filters/brand-filter";
import { SortFilter } from "@/features/shop/products/filters/sort-filter";
import { useAnalyticsTracker } from "@/features/shop/analytics/hooks/use-analytics-tracker";

type Props = {
  brands: string[];
  currentFilters: {
    search?: string;
    brand?: string;
    sort?: string;
  };
  salesRepId?: number;
  onFilterChange?: () => void;
};

export function CatalogFilters({
  brands,
  currentFilters,
  salesRepId,
  onFilterChange,
}: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { trackDebounced } = useAnalyticsTracker();
  const searchDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const updateParam = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString());

    if (!value.trim()) {
      params.delete(key);
    } else {
      params.set(key, value);
    }

    // resetear página al cambiar cualquier filtro
    params.delete("page");

    const query = params.toString();
    router.push(query ? `${pathname}?${query}` : pathname);

    onFilterChange?.();
  };

  // product_search con debounce de 800ms para no disparar por cada tecla
  const handleSearchChange = (value: string) => {
    updateParam("search", value);

    if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);
    if (value.trim()) {
      searchDebounceRef.current = setTimeout(() => {
        trackDebounced({
          event_type: "product_search",
          sales_rep_id: salesRepId,
          source: "catalog_filters",
          metadata_json: { query: value.trim() },
        });
      }, 800);
    }
  };

  const clearFilters = () => {
    router.push(pathname);
    onFilterChange?.();
  };

  const hasActiveFilters = !!(
    currentFilters.search ||
    currentFilters.brand ||
    currentFilters.sort
  );

  return (
    <aside className="h-fit w-full space-y-4 rounded-xl border bg-background p-4 lg:sticky lg:top-24">
      <SearchFilter
        value={currentFilters.search ?? ""}
        onChange={handleSearchChange}
      />

      <BrandFilter
        value={currentFilters.brand ?? ""}
        brands={brands}
        onChange={(value) => updateParam("brand", value)}
      />

      <SortFilter
        value={currentFilters.sort ?? ""}
        onChange={(value) => updateParam("sort", value)}
      />

      {hasActiveFilters && (
        <button
          type="button"
          onClick={clearFilters}
          className="w-full rounded-lg border px-3 py-2 text-sm font-medium transition-colors hover:bg-muted"
        >
          Limpiar filtros
        </button>
      )}
    </aside>
  );
}