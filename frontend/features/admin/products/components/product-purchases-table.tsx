"use client";

import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  PURCHASE_SOURCE_LABELS,
  type ProductPurchase,
} from "@/features/admin/products/purchase-types";

const money = new Intl.NumberFormat("es-AR", {
  style: "currency",
  currency: "ARS",
  maximumFractionDigits: 2,
});

/** "2026-10-04" -> "04/10/2026" (sin pasar por Date: evita corrimientos de zona horaria). */
export function formatDay(value: string | null) {
  if (!value) return "—";
  const [y, m, d] = value.split("-");
  return `${d}/${m}/${y}`;
}

function daysUntil(value: string) {
  const [y, m, d] = value.split("-").map(Number);
  const target = new Date(y, m - 1, d).getTime();
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  return Math.round((target - today) / 86_400_000);
}

function ExpiryCell({ value }: { value: string | null }) {
  if (!value) return <span className="text-muted-foreground">—</span>;
  const days = daysUntil(value);

  return (
    <div className="flex flex-col items-start gap-1">
      <span>{formatDay(value)}</span>
      {days < 0 ? (
        <Badge variant="destructive">Vencido</Badge>
      ) : days <= 30 ? (
        <Badge variant="secondary">Vence en {days} {days === 1 ? "día" : "días"}</Badge>
      ) : null}
    </div>
  );
}

/** Variación del costo respecto de la compra anterior (la fila de abajo, que es más vieja). */
function CostChange({ current, previous }: { current: number; previous: number | undefined }) {
  if (previous === undefined || previous <= 0 || current === previous) return null;
  const pct = ((current - previous) / previous) * 100;
  const up = pct > 0;
  return (
    <span className={up ? "text-xs text-destructive" : "text-xs text-green-600"}>
      {up ? "▲" : "▼"} {Math.abs(pct).toFixed(1)}%
    </span>
  );
}

export function ProductPurchasesTable({ purchases }: { purchases: ProductPurchase[] }) {
  if (purchases.length === 0) {
    return (
      <div className="rounded-2xl border bg-background p-8 text-center text-sm text-muted-foreground shadow-sm">
        Todavía no hay compras registradas para este producto. Usá &quot;Registrar compra&quot;
        para cargar la primera.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-2xl border bg-background shadow-sm">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Fecha</TableHead>
            <TableHead className="text-right">Cantidad</TableHead>
            <TableHead className="text-right">Costo unit.</TableHead>
            <TableHead className="text-right">Remarque</TableHead>
            <TableHead className="text-right">Precio de venta</TableHead>
            <TableHead>Vencimiento</TableHead>
            <TableHead>Origen</TableHead>
            <TableHead>Notas</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {purchases.map((purchase, index) => (
            <TableRow key={purchase.id}>
              <TableCell className="whitespace-nowrap">
                {formatDay(purchase.purchase_date)}
                {purchase.created_by_name && (
                  <p className="text-xs text-muted-foreground">{purchase.created_by_name}</p>
                )}
              </TableCell>
              <TableCell className="text-right font-medium">{purchase.quantity}</TableCell>
              <TableCell className="text-right">
                <div className="flex flex-col items-end">
                  <span className="font-medium">{money.format(Number(purchase.unit_cost))}</span>
                  <CostChange
                    current={Number(purchase.unit_cost)}
                    previous={
                      purchases[index + 1] ? Number(purchases[index + 1].unit_cost) : undefined
                    }
                  />
                </div>
              </TableCell>
              <TableCell className="text-right">
                {purchase.markup_percent != null
                  ? `${Number(purchase.markup_percent)}%`
                  : "—"}
              </TableCell>
              <TableCell className="text-right">
                {purchase.sale_price != null ? money.format(Number(purchase.sale_price)) : "—"}
              </TableCell>
              <TableCell>
                <ExpiryCell value={purchase.expiry_date} />
              </TableCell>
              <TableCell className="whitespace-nowrap">
                <Badge variant="outline">{PURCHASE_SOURCE_LABELS[purchase.source] ?? purchase.source}</Badge>
              </TableCell>
              <TableCell className="max-w-[220px] truncate text-muted-foreground" title={purchase.notes ?? ""}>
                {purchase.notes ?? "—"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
