"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, Truck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { SupplierFilters } from "@/features/admin/suppliers/components/supplier-filters";
import { SuppliersTable } from "@/features/admin/suppliers/components/suppliers-table";
import { useSuppliers } from "@/features/admin/suppliers/hooks/use-suppliers";
import type { SupplierStatusFilter } from "@/features/admin/suppliers/types";

const PAGE_SIZE = 20;

export function SuppliersList() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<SupplierStatusFilter>("");

  const { data, isLoading, error, isFetching } = useSuppliers({
    page,
    page_size: PAGE_SIZE,
    search,
    status,
  });

  function handleSearchChange(value: string) {
    setSearch(value);
    setPage(1);
  }

  function handleStatusChange(value: SupplierStatusFilter) {
    setStatus(value);
    setPage(1);
  }

  const suppliers = data?.suppliers ?? [];
  const total = data?.total ?? 0;
  const totalPages = data?.total_pages ?? 1;
  const currentPage = data?.page ?? 1;
  const pageSize = data?.page_size ?? PAGE_SIZE;

  const startItem = total === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, total);

  return (
    <div className="w-full max-w-full space-y-4 min-w-0">
      <SupplierFilters
        search={search}
        status={status}
        onSearchChange={handleSearchChange}
        onStatusChange={handleStatusChange}
      />

      {/* Barra de conteo y paginación */}
      <div className="flex flex-col gap-4 rounded-2xl border bg-background p-4 shadow-sm xl:flex-row xl:items-center xl:justify-between">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Truck className="h-4 w-4 shrink-0" />
          <div>
            <p>
              Mostrando {startItem}-{endItem} de {total} proveedores
            </p>
            {isFetching && !isLoading ? (
              <p className="text-xs text-muted-foreground/80">Actualizando...</p>
            ) : null}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 sm:flex-nowrap">
          <span className="whitespace-nowrap text-sm text-muted-foreground">
            Página {currentPage} de {totalPages || 1}
          </span>

          <div className="flex w-full items-center gap-2 sm:w-auto">
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
              disabled={currentPage >= totalPages || isLoading}
            >
              Siguiente
              <ChevronRight className="ml-1 h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Contenedor con scroll horizontal aislado para la tabla o el mensaje de 'sin resultados' */}
      {error ? (
        <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          {error instanceof Error ? error.message : "No se pudieron cargar los proveedores."}
        </div>
      ) : isLoading && !data ? (
        <div className="rounded-2xl border bg-background p-6 text-sm text-muted-foreground shadow-sm">
          Cargando proveedores...
        </div>
      ) : (
        <div className="w-full max-w-full overflow-hidden rounded-2xl border bg-background shadow-sm">
          <div className="overflow-x-auto">
            <SuppliersTable suppliers={suppliers} />
          </div>
        </div>
      )}
    </div>
  );
}