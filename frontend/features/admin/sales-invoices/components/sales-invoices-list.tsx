"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, ReceiptText } from "lucide-react";

import { Button } from "@/components/ui/button";
import { SalesInvoiceFilters } from "@/features/admin/sales-invoices/components/sales-invoice-filters";
import { SalesInvoicesTable } from "@/features/admin/sales-invoices/components/sales-invoices-table";
import { useSalesInvoices } from "@/features/admin/sales-invoices/hooks/use-sales-invoices";
import type { SalesInvoiceStatus } from "@/features/admin/sales-invoices/types";

const PAGE_SIZE = 20;

export function SalesInvoicesList() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<SalesInvoiceStatus | "all">("all");

  const { data, isLoading, error, isFetching } = useSalesInvoices({
    page,
    page_size: PAGE_SIZE,
    status,
  });

  const salesInvoices = data?.sales_invoices ?? [];
  const total = data?.total ?? 0;
  const totalPages = data?.total_pages ?? 1;
  const currentPage = data?.page ?? 1;
  const pageSize = data?.page_size ?? PAGE_SIZE;

  const startItem = total === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, total);

  return (
    <div className="space-y-4">
      <SalesInvoiceFilters
        status={status}
        onStatusChange={(nextStatus) => {
          setPage(1);
          setStatus(nextStatus);
        }}
      />

      <div className="rounded-2xl border bg-background p-4 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          
          {/* Info Izquierda */}
          <div className="flex items-center gap-3 min-w-0">
            <div className="rounded-xl border bg-muted/40 p-2 shrink-0">
              <ReceiptText className="h-4 w-4 text-muted-foreground" />
            </div>
            <div className="min-w-0 space-y-0.5">
              <p className="text-sm font-semibold tracking-tight">Remitos de venta</p>
              <p className="text-xs sm:text-sm text-muted-foreground truncate">
                Mostrando {startItem}-{endItem} de <span className="font-medium text-foreground">{total}</span> registros.
              </p>
              {isFetching && !isLoading && (
                <p className="text-[11px] font-medium text-kraft animate-pulse">
                  Actualizando datos...
                </p>
              )}
            </div>
          </div>

          {/* Paginación Derecha */}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-end w-full md:w-auto">
            <span className="text-xs sm:text-sm text-muted-foreground text-center sm:text-right sm:min-w-[110px] md:order-2">
              Página <span className="font-medium text-foreground">{currentPage}</span> de {totalPages}
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
          {error instanceof Error ? error.message : "No se pudieron cargar las remitos de venta."}
        </div>
      ) : isLoading && !data ? (
        <div className="rounded-2xl border bg-background p-8 text-center text-sm text-muted-foreground shadow-sm animate-pulse">
          Cargando remitos de venta...
        </div>
      ) : (
        <SalesInvoicesTable salesInvoices={salesInvoices} />
      )}
    </div>
  );
}