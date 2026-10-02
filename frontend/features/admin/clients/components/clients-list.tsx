"use client";

import { useState } from "react";
import { ClientFilters } from "@/features/admin/clients/components/client-filters";
import { ClientsTable } from "@/features/admin/clients/components/clients-table";
import { ClientPagination } from "@/features/admin/clients/components/client-pagination";
import { useClients } from "@/features/admin/clients/hooks/use-clients";

export function ClientsList() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<"" | "active" | "inactive">("");
  const [sort, setSort] = useState<"" | "name" | "created_at">("created_at");
  const [page, setPage] = useState(1);

  const pageSize = 20;

  const { data, isLoading, isError, error, isFetching } = useClients({
    page,
    page_size: pageSize,
    search,
    status,
    sort,
  });

  function handleSearchChange(value: string) {
    setSearch(value);
    setPage(1);
  }

  function handleStatusChange(value: "" | "active" | "inactive") {
    setStatus(value);
    setPage(1);
  }

  function handleSortChange(value: "" | "name" | "created_at") {
    setSort(value);
    setPage(1);
  }

  if (isLoading && !data) {
    return <p className="text-sm text-muted-foreground">Cargando clientes...</p>;
  }

  if (isError) {
    return (
      <p className="text-sm text-destructive">
        {error instanceof Error ? error.message : "Error al cargar clientes"}
      </p>
    );
  }

  const total = data?.total ?? 0;
  const currentPage = data?.page ?? 1;
  const totalPages = data?.total_pages ?? 1;
  const pageSizeFromApi = data?.page_size ?? pageSize;
  const startItem = total === 0 ? 0 : (currentPage - 1) * pageSizeFromApi + 1;
  const endItem = Math.min(currentPage * pageSizeFromApi, total);

  return (
    <div className="space-y-4">
      <ClientFilters
        search={search}
        status={status}
        sort={sort}
        onSearchChange={handleSearchChange}
        onStatusChange={handleStatusChange}
        onSortChange={handleSortChange}
      />

      <div className="flex flex-col gap-3 rounded-2xl border bg-background p-4 shadow-sm md:flex-row md:items-center md:justify-between">
        <div className="text-sm text-muted-foreground">
          Mostrando {startItem}-{endItem} de {total} clientes
          {isFetching && !isLoading ? (
            <span className="ml-2 text-xs">Actualizando...</span>
          ) : null}
        </div>

        <div className="text-sm text-muted-foreground">Página {currentPage} de {totalPages}</div>
      </div>

      <ClientsTable clients={data?.clients ?? []} />

      <ClientPagination
        page={currentPage}
        totalPages={totalPages}
        onPageChange={setPage}
      />
    </div>
  );
}