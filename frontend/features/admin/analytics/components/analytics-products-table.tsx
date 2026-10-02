"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { AnalyticsProductDaily } from "@/features/admin/analytics/schemas/analytics-schema";
import { getProductApi } from "@/features/admin/products/apis/products-api";
import { useQueries } from "@tanstack/react-query";

type Props = {
  data: AnalyticsProductDaily[];
  isLoading: boolean;
  isError: boolean;
};

function formatCurrency(value: string | number): string {
  const num = typeof value === "string" ? parseFloat(value) : value;
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 0,
  }).format(num);
}

function formatMarginPct(revenue: string, margin: string): string {
  const rev = parseFloat(revenue);
  const mar = parseFloat(margin);
  if (!rev) return "—";
  return `${((mar / rev) * 100).toFixed(1)}%`;
}

export function AnalyticsProductsTable({ data, isLoading, isError }: Props) {
  // Fetch product names for all product IDs in the data
  const productQueries = useQueries({
    queries: data.map((row) => ({
      queryKey: ["product", row.product_id],
      queryFn: () => getProductApi(row.product_id),
      staleTime: 5 * 60 * 1000, // 5 min cache
    })),
  });

  // Build a map of product_id -> name
  const productNames = Object.fromEntries(
    productQueries
      .map((q, i) => [data[i]?.product_id, q.data?.name])
      .filter(([, name]) => name != null)
  );

  if (isLoading) {
    return (
      <div className="rounded-xl border">
        <div className="divide-y">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4 px-4 py-3">
              <div className="h-4 w-40 rounded bg-muted" />
              <div className="h-4 w-16 rounded bg-muted" />
              <div className="h-4 w-20 rounded bg-muted" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-xl border px-4 py-6 text-center text-sm text-destructive">
        Error al cargar métricas de productos.
      </div>
    );
  }

  if (!data.length) {
    return (
      <div className="rounded-xl border px-4 py-8 text-center text-sm text-muted-foreground">
        Sin datos para la fecha seleccionada.
      </div>
    );
  }

  // Sort by quantity sold descending
  const sorted = [...data].sort((a, b) => b.quantity_sold - a.quantity_sold);

  return (
    <div className="rounded-xl border">
      {/* Mobile: tarjetas */}
      <div className="divide-y md:hidden">
        {sorted.map((row) => (
          <div key={row.id} className="px-4 py-3">
            <div className="flex items-center justify-between gap-3">
              <span className="truncate font-medium">
                {productNames[row.product_id] ?? `#${row.product_id}`}
              </span>
              <span className="shrink-0 font-semibold">
                {formatCurrency(row.revenue_generated)}
              </span>
            </div>
            <div className="mt-2 grid grid-cols-2 gap-y-1 text-xs text-muted-foreground">
              <span>
                Unidades:{" "}
                <span className="text-foreground">{row.quantity_sold}</span>
              </span>
              <span>
                Margen %:{" "}
                <span className="text-foreground">
                  {formatMarginPct(row.revenue_generated, row.margin_generated)}
                </span>
              </span>
              <span>
                Costo:{" "}
                <span className="text-foreground">
                  {formatCurrency(row.cost_generated)}
                </span>
              </span>
              <span>
                Margen:{" "}
                <span className="text-foreground">
                  {formatCurrency(row.margin_generated)}
                </span>
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Desktop / tablet: tabla */}
      <div className="hidden md:block">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Producto</TableHead>
              <TableHead className="text-right">Unidades</TableHead>
              <TableHead className="text-right">Ingresos</TableHead>
              <TableHead className="text-right">Costo</TableHead>
              <TableHead className="text-right">Margen</TableHead>
              <TableHead className="text-right">Margen %</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sorted.map((row) => (
              <TableRow key={row.id}>
                <TableCell className="font-medium">
                  {productNames[row.product_id] ?? `#${row.product_id}`}
                </TableCell>
                <TableCell className="text-right">{row.quantity_sold}</TableCell>
                <TableCell className="text-right">{formatCurrency(row.revenue_generated)}</TableCell>
                <TableCell className="text-right">{formatCurrency(row.cost_generated)}</TableCell>
                <TableCell className="text-right">{formatCurrency(row.margin_generated)}</TableCell>
                <TableCell className="text-right text-muted-foreground">
                  {formatMarginPct(row.revenue_generated, row.margin_generated)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}