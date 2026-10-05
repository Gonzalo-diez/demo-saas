"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useProduct } from "@/features/admin/products/hooks/use-product";
import { useProductPurchases } from "@/features/admin/products/hooks/use-product-purchases";
import { ProductPurchasesTable, formatDay } from "@/features/admin/products/components/product-purchases-table";
import { RegisterPurchaseDialog } from "@/features/admin/products/components/register-purchase-dialog";

const PAGE_SIZE = 20;

const money = new Intl.NumberFormat("es-AR", {
  style: "currency",
  currency: "ARS",
  maximumFractionDigits: 2,
});

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-2xl border bg-background p-4 shadow-sm">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
      {hint && <p className="mt-0.5 text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

export function ProductPurchasesPageContent({ productId }: { productId: number }) {
  const [page, setPage] = useState(1);

  const productQuery = useProduct(productId);
  const purchasesQuery = useProductPurchases(productId, page, PAGE_SIZE);

  const product = productQuery.data;
  const data = purchasesQuery.data;
  const summary = data?.summary;

  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const error = productQuery.error ?? purchasesQuery.error;
  const isLoading = productQuery.isLoading || purchasesQuery.isLoading;

  const optionalMoney = (value: number | null | undefined) =>
    value == null ? "—" : money.format(Number(value));

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="space-y-2">
          <Link
            href="/admin/products"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            Volver a productos
          </Link>
          <div>
            <h2 className="text-2xl font-semibold">Historial de compras</h2>
            <p className="text-sm text-muted-foreground">
              {product?.name ?? `Producto #${productId}`}
              {product && (
                <>
                  {" · "}Stock {product.stock_current} · Costo prom. {money.format(Number(product.unit_cost))} ·
                  Venta {money.format(Number(product.unit_price))}
                  {product.markup_percent != null && ` (${Number(product.markup_percent)}% de remarque)`}
                </>
              )}
            </p>
          </div>
        </div>

        {product && <RegisterPurchaseDialog product={product} />}
      </div>

      {summary && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Stat
            label="Costo promedio ponderado"
            value={optionalMoney(summary.average_cost)}
            hint={`${summary.purchases_count} compras · ${summary.total_quantity} unidades`}
          />
          <Stat label="Último costo" value={optionalMoney(summary.last_cost)} />
          <Stat
            label="Costo mínimo / máximo"
            value={`${optionalMoney(summary.min_cost)} / ${optionalMoney(summary.max_cost)}`}
          />
          <Stat
            label="Próximo vencimiento"
            value={formatDay(summary.next_expiry_date)}
            hint="Referencia: no descuenta lo ya vendido"
          />
        </div>
      )}

      {error ? (
        <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          {error instanceof Error ? error.message : "No se pudo cargar el historial de compras."}
        </div>
      ) : isLoading ? (
        <div className="rounded-2xl border bg-background p-6 text-sm text-muted-foreground shadow-sm">
          Cargando historial...
        </div>
      ) : (
        <>
          <ProductPurchasesTable purchases={data?.items ?? []} />

          {totalPages > 1 && (
            <div className="flex items-center justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                <ChevronLeft className="mr-1 h-4 w-4" />
                Anterior
              </Button>
              <span className="min-w-[120px] text-center text-sm text-muted-foreground">
                Página {page} de {totalPages}
              </span>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                Siguiente
                <ChevronRight className="ml-1 h-4 w-4" />
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
