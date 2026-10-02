"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, Receipt } from "lucide-react";

import { Button } from "@/components/ui/button";
import { PurchaseInvoiceFilters } from "@/features/admin/purchase-invoices/components/purchase-invoice-filters";
import { PurchaseInvoicesTable } from "@/features/admin/purchase-invoices/components/purchase-invoices-table";
import { usePurchaseInvoices } from "@/features/admin/purchase-invoices/hooks/use-purchase-invoices";
import type { PurchaseInvoiceStatus } from "@/features/admin/purchase-invoices/types";

const PAGE_SIZE = 20;

export function PurchaseInvoicesList() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<PurchaseInvoiceStatus | "all">("all");

  const { data, isLoading, error, isFetching } = usePurchaseInvoices({
    page,
    page_size: PAGE_SIZE,
    status,
  });

  const purchaseInvoices = data?.purchase_invoices ?? [];
  const total = data?.total ?? 0;
  const totalPages = data?.total_pages ?? 1;
  const currentPage = data?.page ?? 1;
  const pageSize = data?.page_size ?? PAGE_SIZE;

  const startItem = total === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, total);

  return (
    <div className="space-y-4">
      <PurchaseInvoiceFilters
        status={status}
        onStatusChange={(nextStatus) => {
          setPage(1);
          setStatus(nextStatus);
        }}
      />

      <div className="rounded-2xl border bg-background p-4 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex min-w-0 items-start gap-3">
            <div className="rounded-xl border bg-muted/40 p-2">
              <Receipt className="h-4 w-4" />
            </div>

            <div className="min-w-0 space-y-1">
              <p className="text-sm font-medium">Remitos de compra</p>
              <p className="text-sm text-muted-foreground">
                Mostrando {startItem}-{endItem} de {total} registros.
              </p>
              {isFetching && !isLoading && (
                <p className="text-xs text-muted-foreground">Actualizando datos...</p>
              )}
            </div>
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
      </div>

      {error ? (
        <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          {error instanceof Error
            ? error.message
            : "No se pudieron cargar las remitos de compra."}
        </div>
      ) : isLoading && !data ? (
        <div className="rounded-2xl border bg-background p-6 text-sm text-muted-foreground shadow-sm">
          Cargando remitos de compra...
        </div>
      ) : (
        <PurchaseInvoicesTable purchaseInvoices={purchaseInvoices} />
      )}
    </div>
  );
}