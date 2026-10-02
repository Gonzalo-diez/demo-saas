"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SalesRepFilters } from "@/features/admin/sales-reps/components/sales-rep-filters";
import { SalesRepsTable } from "@/features/admin/sales-reps/components/sales-reps-table";
import { useSalesReps } from "@/features/admin/sales-reps/hooks/use-sales-reps";
import type {
  SalesRepSort,
  SalesRepStatusFilter,
} from "@/features/admin/sales-reps/types";

const PAGE_SIZE = 20;

export function SalesRepsList() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<SalesRepStatusFilter>("");
  const [sort, setSort] = useState<SalesRepSort>("created_at");
  const [page, setPage] = useState(1);

  const { data, isLoading, error, isFetching } = useSalesReps({
    page,
    page_size: PAGE_SIZE,
    search,
    status,
    sort,
  });

  function handleSearchChange(value: string) {
    setSearch(value);
    setPage(1);
  }

  function handleStatusChange(value: SalesRepStatusFilter) {
    setStatus(value);
    setPage(1);
  }
  
  function handleSortChange(value: SalesRepSort) {
    setSort(value);
    setPage(1);
  }

  const salesReps = data?.sales_reps ?? [];
  const total = data?.total ?? 0;
  const totalPages = data?.total_pages ?? 1;
  const currentPage = data?.page ?? 1;
  const pageSize = data?.page_size ?? PAGE_SIZE;

  const startItem = total === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, total);

  return (
    <div className="space-y-4">
      <SalesRepFilters
        search={search}
        status={status}
        sort={sort}
        onSearchChange={handleSearchChange}
        onStatusChange={handleStatusChange}
        onSortChange={handleSortChange}
      />

      <div className="flex flex-col gap-3 rounded-2xl border bg-background p-4 shadow-sm md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Users className="h-4 w-4" />
          <span>
            Mostrando {startItem}-{endItem} de {total} vendedores
          </span>
          {isFetching && !isLoading && (
            <span className="text-xs text-muted-foreground">
              Actualizando...
            </span>
          )}
        </div>

        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-end">
            <span className="text-sm text-muted-foreground sm:order-2 sm:min-w-[130px] sm:text-right">
              Página {currentPage} de {totalPages}
            </span>

            <div className="flex gap-2 sm:order-1">
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="flex-1 sm:flex-none"
                onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                disabled={currentPage === 1 || isLoading}
              >
                <ChevronLeft className="mr-1 h-4 w-4" />
                Anterior
              </Button>

              <Button
                type="button"
                variant="outline"
                size="sm"
                className="flex-1 sm:flex-none"
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
            : "No se pudieron cargar los vendedores"}
        </div>
      ) : isLoading && !data ? (
        <div className="rounded-2xl border bg-background p-6 text-sm text-muted-foreground shadow-sm">
          Cargando vendedores...
        </div>
      ) : (
        <SalesRepsTable salesReps={salesReps} />
      )}
    </div>
  );
}