"use client";

import { useState } from "react";
import Link from "next/link";
import { ChevronLeft, ChevronRight, ArrowLeft, History } from "lucide-react";

import { Button } from "@/components/ui/button";
import { InventoryMovementsTable } from "@/features/admin/inventory-movements/components/inventory-movements-table";
import { useProductInventoryMovements } from "@/features/admin/inventory-movements/hooks/use-product-inventory-movements";
import { useProduct } from "@/features/admin/products/hooks/use-product";

type ProductInventoryMovementsPageContentProps = {
  productId: number;
};

const PAGE_SIZE = 20;

export function ProductInventoryMovementsPageContent({
  productId,
}: ProductInventoryMovementsPageContentProps) {
  const [page, setPage] = useState(1);

  const productQuery = useProduct(productId);
  const movementsQuery = useProductInventoryMovements({
    productId,
    page,
    pageSize: PAGE_SIZE,
  });

  const product = productQuery.data;
  const data = movementsQuery.data;

  const movements = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = data?.total_pages ?? 1;
  const currentPage = data?.page ?? 1;
  const pageSize = data?.page_size ?? PAGE_SIZE;

  const startItem = total === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, total);

  const isLoading = productQuery.isLoading || movementsQuery.isLoading;
  const error = productQuery.error ?? movementsQuery.error;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="space-y-2">
          <Link
            href="/products"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            Volver a productos
          </Link>

          <div>
            <h2 className="text-2xl font-semibold">Historial de inventario</h2>
            <p className="text-sm text-muted-foreground">
              {product?.name ?? `Producto #${productId}`}
            </p>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-3 rounded-2xl border bg-background p-4 shadow-sm md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <History className="h-4 w-4" />
          <span>
            Mostrando {startItem}-{endItem} de {total} movimientos
          </span>
          {movementsQuery.isFetching && !movementsQuery.isLoading && (
            <span className="text-xs text-muted-foreground">Actualizando...</span>
          )}
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
      ) : isLoading ? (
        <div className="rounded-2xl border bg-background p-6 text-sm text-muted-foreground shadow-sm">
          Cargando historial...
        </div>
      ) : (
        <InventoryMovementsTable inventoryMovements={movements} />
      )}
    </div>
  );
}