"use client";

import { useState, Fragment } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { AnalyticsClientDaily } from "@/features/admin/analytics/schemas/analytics-schema";
import { getClientApi } from "@/features/admin/clients/apis/clients-api";
import { useQueries } from "@tanstack/react-query";

type Props = {
  data: AnalyticsClientDaily[];
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

export function AnalyticsClientsTable({ data, isLoading, isError }: Props) {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  // Fetch client names for all client IDs in the data
  const clientQueries = useQueries({
    queries: data.map((row) => ({
      queryKey: ["client", row.client_id],
      queryFn: () => getClientApi(row.client_id),
      staleTime: 5 * 60 * 1000, // 5 min cache
    })),
  });

  const clientNames = Object.fromEntries(
    clientQueries
      .map((q, i) => [data[i]?.client_id, q.data?.name])
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
        Error al cargar métricas de clientes.
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

  // Sort by revenue descending
  const sorted = [...data].sort(
    (a, b) => parseFloat(b.revenue_generated) - parseFloat(a.revenue_generated)
  );

  return (
    <div className="rounded-xl border">
      {/* Mobile: tarjetas */}
      <div className="divide-y md:hidden">
        {sorted.map((row) => {
          const isExpanded = expandedId === row.client_id;
          return (
            <Fragment key={row.id}>
              <button
                type="button"
                onClick={() =>
                  setExpandedId(isExpanded ? null : row.client_id)
                }
                className="flex w-full items-start justify-between gap-3 px-4 py-3 text-left"
              >
                <span className="flex min-w-0 items-center gap-2">
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
                  )}
                  <span className="truncate font-medium">
                    {clientNames[row.client_id] ?? `#${row.client_id}`}
                  </span>
                </span>
                <span className="shrink-0 font-semibold">
                  {formatCurrency(row.revenue_generated)}
                </span>
              </button>
              <div className="grid grid-cols-2 gap-y-1 px-4 pb-3 text-xs text-muted-foreground">
                <span>
                  Pedidos:{" "}
                  <span className="text-foreground">{row.total_orders}</span>
                </span>
                <span>
                  Productos únicos:{" "}
                  <span className="text-foreground">
                    {row.unique_products_count}
                  </span>
                </span>
                <span>
                  Margen:{" "}
                  <span className="text-foreground">
                    {formatCurrency(row.margin_generated)}
                  </span>
                </span>
                <span>
                  Margen %:{" "}
                  <span className="text-foreground">
                    {formatMarginPct(row.revenue_generated, row.margin_generated)}
                  </span>
                </span>
              </div>
              {isExpanded && (
                <div className="bg-muted/30">
                  <ClientPurchaseDetail row={row} />
                </div>
              )}
            </Fragment>
          );
        })}
      </div>

      {/* Desktop / tablet: tabla */}
      <div className="hidden md:block">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-8" />
              <TableHead>Cliente</TableHead>
              <TableHead className="text-right">Pedidos</TableHead>
              <TableHead className="text-right">Productos únicos</TableHead>
              <TableHead className="text-right">Ingresos</TableHead>
              <TableHead className="text-right">Costo</TableHead>
              <TableHead className="text-right">Margen</TableHead>
              <TableHead className="text-right">Margen %</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sorted.map((row) => {
              const isExpanded = expandedId === row.client_id;
              return (
                <Fragment key={row.client_id ?? row.id}>
                  <TableRow
                    key={row.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() =>
                      setExpandedId(isExpanded ? null : row.client_id)
                    }
                  >
                    <TableCell>
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      )}
                    </TableCell>
                    <TableCell className="font-medium">
                      {clientNames[row.client_id] ?? `#${row.client_id}`}
                    </TableCell>
                    <TableCell className="text-right">{row.total_orders}</TableCell>
                    <TableCell className="text-right">{row.unique_products_count}</TableCell>
                    <TableCell className="text-right">{formatCurrency(row.revenue_generated)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(row.cost_generated)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(row.margin_generated)}</TableCell>
                    <TableCell className="text-right text-muted-foreground">
                      {formatMarginPct(row.revenue_generated, row.margin_generated)}
                    </TableCell>
                  </TableRow>
                  {isExpanded && (
                    <Fragment>
                      <TableRow key={`${row.id}-detail`} className="bg-muted/30 hover:bg-muted/30">
                        <TableCell colSpan={8} className="p-0">
                          <ClientPurchaseDetail row={row} />
                        </TableCell>
                      </TableRow>
                    </Fragment>
                  )}
                </Fragment>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

function ClientPurchaseDetail({ row }: { row: AnalyticsClientDaily }) {
  const products = [...row.products_bought].sort(
    (a, b) => parseFloat(b.amount) - parseFloat(a.amount)
  );
  const categories = [...(row.categories_summary ?? [])].sort(
    (a, b) => parseFloat(b.amount) - parseFloat(a.amount)
  );

  return (
    <div className="grid grid-cols-1 gap-6 px-6 py-4 md:grid-cols-2">
      <div>
        <h4 className="mb-2 text-xs font-semibold uppercase text-muted-foreground">
          Productos comprados
        </h4>
        {products.length === 0 ? (
          <p className="text-sm text-muted-foreground">Sin productos registrados.</p>
        ) : (
          <ul className="space-y-1.5">
            {products.map((p) => (
              <li
                key={p.product_id}
                className="flex items-center justify-between gap-3 text-sm"
              >
                <span className="truncate">
                  {p.product_name ?? `#${p.product_id}`}
                  {p.category && (
                    <span className="ml-2 text-xs text-muted-foreground">
                      ({p.category})
                    </span>
                  )}
                </span>
                <span className="shrink-0 tabular-nums text-muted-foreground">
                  {p.qty} u. — {formatCurrency(p.amount)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div>
        <h4 className="mb-2 text-xs font-semibold uppercase text-muted-foreground">
          Por categoría
        </h4>
        {categories.length === 0 ? (
          <p className="text-sm text-muted-foreground">Sin categorías registradas.</p>
        ) : (
          <ul className="space-y-1.5">
            {categories.map((c) => (
              <li
                key={c.category}
                className="flex items-center justify-between gap-3 text-sm"
              >
                <span className="truncate">
                  {c.category}
                  <span className="ml-2 text-xs text-muted-foreground">
                    ({c.unique_products} prod.)
                  </span>
                </span>
                <span className="shrink-0 tabular-nums text-muted-foreground">
                  {c.qty} u. — {formatCurrency(c.amount)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}