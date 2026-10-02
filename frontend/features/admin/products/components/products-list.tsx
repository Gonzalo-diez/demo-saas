"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, PackageSearch } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useProducts } from "@/features/admin/products/hooks/use-products";
import { ProductsTable } from "@/features/admin/products/components/products-table";
import { ProductsSearch } from "@/features/admin/products/components/products-search";
import type { ProductSort, ProductStatusFilter } from "@/features/admin/products/types";

const PAGE_SIZE = 20;

export function ProductsList() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<ProductStatusFilter>("all");
  const [brand, setBrand] = useState("");
  const [sort, setSort] = useState<ProductSort>("");
  const [page, setPage] = useState(1);

  const { data, isLoading, error, isFetching } = useProducts({
    page,
    page_size: PAGE_SIZE,
    search,
    status,
    brand,
    sort,
  });

  function handleSearchChange(value: string) {
    setSearch(value);
    setPage(1);
  }

  function handleStatusChange(value: ProductStatusFilter) {
    setStatus(value);
    setPage(1);
  }
  
  function handleBrandChange(value: string) {
    setBrand(value);
    setPage(1);
  }

  function handleSortChange(value: ProductSort) {
    setSort(value);
    setPage(1);
  }

  const products = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = data?.total_pages ?? 1;
  const currentPage = data?.page ?? 1;
  const pageSize = data?.page_size ?? PAGE_SIZE;

  const startItem = total === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, total);

  return (
    <div className="space-y-4">
      <ProductsSearch
        value={search}
        onChange={handleSearchChange}
        status={status}
        onStatusChange={handleStatusChange}
        brand={brand}
        onBrandChange={handleBrandChange}
        sort={sort}
        onSortChange={handleSortChange}
      />

      <div className="rounded-2xl border bg-background p-4 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-col gap-1 text-sm text-muted-foreground sm:flex-row sm:items-center sm:gap-2">
            <div className="flex items-center gap-2">
              <PackageSearch className="h-4 w-4 shrink-0" />
              <span>
                Mostrando {startItem}-{endItem} de {total} productos
              </span>
            </div>

            {isFetching && !isLoading && (
              <span className="text-xs text-muted-foreground">Actualizando...</span>
            )}
          </div>

          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-end">
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="w-full sm:w-auto"
              onClick={() => setPage((prev) => Math.max(1, prev - 1))}
              disabled={currentPage === 1 || isLoading}
            >
              <ChevronLeft className="mr-1 h-4 w-4" />
              Anterior
            </Button>

            <span className="text-center text-sm text-muted-foreground sm:min-w-[140px]">
              Página {currentPage} de {totalPages}
            </span>

            <Button
              type="button"
              variant="outline"
              size="sm"
              className="w-full sm:w-auto"
              onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages || isLoading}
            >
              Siguiente
              <ChevronRight className="ml-1 h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {error ? (
        <div className="rounded-2xl border border-destructive/20 bg-destructive/10 p-6 text-sm text-destructive shadow-sm">
          {error instanceof Error
            ? error.message
            : "No se pudieron cargar los productos"}
        </div>
      ) : isLoading && !data ? (
        <div className="rounded-2xl border bg-background p-6 text-sm text-muted-foreground shadow-sm">
          Cargando productos...
        </div>
      ) : (
        <ProductsTable products={products} />
      )}
    </div>
  );
}