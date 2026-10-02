"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, History } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { InventoryMovementsTable } from "@/features/admin/inventory-movements/components/inventory-movements-table";
import { useProductInventoryMovements } from "@/features/admin/inventory-movements/hooks/use-product-inventory-movements";

type ProductInventoryHistoryDialogProps = {
  productId: number;
  productName: string;
};

const PAGE_SIZE = 20;

export function ProductInventoryHistoryDialog({
  productId,
  productName,
}: ProductInventoryHistoryDialogProps) {
  const [open, setOpen] = useState(false);
  const [page, setPage] = useState(1);

  const { data, isLoading, error, isFetching } = useProductInventoryMovements({
    productId: open ? productId : null,
    page,
    pageSize: PAGE_SIZE,
  });

  const movements = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = data?.total_pages ?? 1;
  const currentPage = data?.page ?? 1;
  const pageSize = data?.page_size ?? PAGE_SIZE;

  const startItem = total === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, total);

  return (
    <Dialog
      open={open}
      onOpenChange={(nextOpen) => {
        setOpen(nextOpen);
        if (!nextOpen) setPage(1);
      }}
    >
      <DialogTrigger asChild>
        <Button type="button" variant="outline">
          <History className="mr-2 h-4 w-4" />
          Historial
        </Button>
      </DialogTrigger>

      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-6xl">
        <DialogHeader>
          <DialogTitle>Historial de inventario</DialogTitle>
          <DialogDescription>{productName}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="flex flex-col gap-3 rounded-2xl border bg-background p-4 shadow-sm md:flex-row md:items-center md:justify-between">
            <div className="text-sm text-muted-foreground">
              Mostrando {startItem}-{endItem} de {total} movimientos
              {isFetching && !isLoading ? " · Actualizando..." : ""}
            </div>

            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                disabled={currentPage === 1 || isLoading}
              >
                <ChevronLeft className="mr-1 h-4 w-4" />
                Anterior
              </Button>

              <span className="min-w-[120px] text-center text-sm text-muted-foreground">
                Página {currentPage} de {totalPages}
              </span>

              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages || isLoading}
              >
                Siguiente
                <ChevronRight className="ml-1 h-4 w-4" />
              </Button>
            </div>
          </div>

          {error ? (
            <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
              {error instanceof Error
                ? error.message
                : "No se pudo cargar el historial del producto."}
            </div>
          ) : isLoading && !data ? (
            <div className="rounded-2xl border bg-background p-6 text-sm text-muted-foreground shadow-sm">
              Cargando historial...
            </div>
          ) : (
            <InventoryMovementsTable inventoryMovements={movements} />
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}