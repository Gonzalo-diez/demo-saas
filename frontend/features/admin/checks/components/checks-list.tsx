"use client";

import { useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Landmark } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ChecksFilters } from "@/features/admin/checks/components/checks-filters";
import { ChecksTable } from "@/features/admin/checks/components/checks-table";
import { useChecks } from "@/features/admin/checks/hooks/use-checks";
import type { CheckDirection, CheckStatus } from "@/features/admin/checks/types";
import { useClients } from "@/features/admin/clients/hooks/use-clients";
import { useSuppliers } from "@/features/admin/suppliers/hooks/use-suppliers";

const PAGE_SIZE = 20;

export function ChecksList() {
  const [page, setPage] = useState(1);
  const [direction, setDirection] = useState<CheckDirection | "all">("all");
  const [status, setStatus] = useState<CheckStatus | "all">("all");

  const { data, isLoading, error, isFetching } = useChecks({
    page,
    page_size: PAGE_SIZE,
    direction,
    status,
  });

  const clientsQuery = useClients({
    page: 1,
    page_size: 100,
    search: "",
    status: "active",
    sort: "name",
  });

  const suppliersQuery = useSuppliers({ page: 1, page_size: 100, search: "", status: "active" });

  const clientNameById = useMemo(() => {
    const map: Record<number, string> = {};
    for (const client of clientsQuery.data?.clients ?? []) {
      map[client.id] = client.name;
    }
    return map;
  }, [clientsQuery.data]);

  const supplierNameById = useMemo(() => {
    const map: Record<number, string> = {};
    for (const supplier of suppliersQuery.data?.suppliers ?? []) {
      map[supplier.id] = supplier.name;
    }
    return map;
  }, [suppliersQuery.data]);

  const checks = data?.checks ?? [];
  const total = data?.total ?? 0;
  const totalPages = data?.total_pages ?? 1;
  const currentPage = data?.page ?? 1;
  const pageSize = data?.page_size ?? PAGE_SIZE;

  const startItem = total === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, total);

  return (
    <div className="space-y-4">
      <ChecksFilters
        direction={direction}
        status={status}
        onDirectionChange={(value) => {
          setPage(1);
          setDirection(value);
        }}
        onStatusChange={(value) => {
          setPage(1);
          setStatus(value);
        }}
      />

      <div className="rounded-2xl border bg-background p-4 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <div className="rounded-xl border bg-muted/40 p-2 shrink-0">
              <Landmark className="h-4 w-4 text-muted-foreground" />
            </div>
            <div className="min-w-0 space-y-0.5">
              <p className="text-sm font-semibold tracking-tight">Cheques en cartera</p>
              <p className="text-xs sm:text-sm text-muted-foreground truncate">
                Mostrando {startItem}-{endItem} de{" "}
                <span className="font-medium text-foreground">{total}</span> registros.
              </p>
              {isFetching && !isLoading && (
                <p className="text-[11px] font-medium text-kraft animate-pulse">
                  Actualizando datos...
                </p>
              )}
            </div>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-end w-full md:w-auto">
            <span className="text-xs sm:text-sm text-muted-foreground text-center sm:text-right sm:min-w-[110px] md:order-2">
              Página <span className="font-medium text-foreground">{currentPage}</span> de{" "}
              {totalPages}
            </span>

            <div className="flex gap-2 w-full sm:w-auto md:order-1">
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="flex-1 sm:flex-none h-9 text-xs sm:text-sm"
                onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                disabled={currentPage === 1 || isLoading}
              >
                <ChevronLeft className="mr-1 h-4 w-4 shrink-0" />
                Anterior
              </Button>

              <Button
                type="button"
                variant="outline"
                size="sm"
                className="flex-1 sm:flex-none h-9 text-xs sm:text-sm"
                onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages || isLoading}
              >
                Siguiente
                <ChevronRight className="ml-1 h-4 w-4 shrink-0" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {error ? (
        <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive break-words">
          {error instanceof Error ? error.message : "No se pudieron cargar los cheques."}
        </div>
      ) : isLoading && !data ? (
        <div className="rounded-2xl border bg-background p-8 text-center text-sm text-muted-foreground shadow-sm animate-pulse">
          Cargando cheques...
        </div>
      ) : (
        <ChecksTable
          checks={checks}
          clientNameById={clientNameById}
          supplierNameById={supplierNameById}
        />
      )}
    </div>
  );
}
