"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { AnalyticsSalesRepDaily } from "@/features/admin/analytics/schemas/analytics-schema";

type Props = {
  data: AnalyticsSalesRepDaily[];
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

export function AnalyticsSalesRepsTable({ data, isLoading, isError }: Props) {
  if (isLoading) {
    return (
      <div className="rounded-xl border">
        <div className="divide-y">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4 px-4 py-3">
              <div className="h-4 w-24 rounded bg-muted" />
              <div className="h-4 w-20 rounded bg-muted" />
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
        Error al cargar métricas de vendedores.
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
      {/* Vista mobile: cards */}
      <div className="space-y-3 p-3 md:hidden">
        {sorted.map((row) => (
          <div key={row.id} className="space-y-3 rounded-xl border bg-background p-3 text-sm">
            <p className="font-semibold">Vendedor #{row.sales_rep_id}</p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs text-muted-foreground">Pedidos</p>
                <p className="font-medium">{row.total_orders}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Clientes</p>
                <p className="font-medium">{row.total_clients}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Productos vendidos</p>
                <p className="font-medium">{row.total_products_sold}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Margen %</p>
                <p className="font-medium">
                  {formatMarginPct(row.revenue_generated, row.margin_generated)}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Ingresos</p>
                <p className="font-medium">{formatCurrency(row.revenue_generated)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Costo</p>
                <p className="font-medium">{formatCurrency(row.cost_generated)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Margen</p>
                <p className="font-medium">{formatCurrency(row.margin_generated)}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Vista desktop: tabla */}
      <div className="hidden overflow-x-auto md:block">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Vendedor ID</TableHead>
            <TableHead className="text-right">Pedidos</TableHead>
            <TableHead className="text-right">Clientes</TableHead>
            <TableHead className="text-right">Productos vendidos</TableHead>
            <TableHead className="text-right">Ingresos</TableHead>
            <TableHead className="text-right">Costo</TableHead>
            <TableHead className="text-right">Margen</TableHead>
            <TableHead className="text-right">Margen %</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sorted.map((row) => (
            <TableRow key={row.id}>
              <TableCell className="font-medium">#{row.sales_rep_id}</TableCell>
              <TableCell className="text-right">{row.total_orders}</TableCell>
              <TableCell className="text-right">{row.total_clients}</TableCell>
              <TableCell className="text-right">{row.total_products_sold}</TableCell>
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