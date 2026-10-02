"use client";

import type { SalesInvoiceItem } from "@/features/admin/sales-invoices/types";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type SalesInvoiceItemsTableProps = {
  items: SalesInvoiceItem[];
};

function formatMoney(value: string | null) {
  const numericValue = Number(value ?? 0);

  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 2,
  }).format(Number.isNaN(numericValue) ? 0 : numericValue);
}

export function SalesInvoiceItemsTable({
  items,
}: SalesInvoiceItemsTableProps) {
  return (
    <div className="overflow-hidden rounded-xl border">
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID producto</TableHead>
              <TableHead>Cantidad</TableHead>
              <TableHead>Costo unitario</TableHead>
              <TableHead>Precio unitario</TableHead>
              <TableHead>Subtotal costo</TableHead>
              <TableHead>Subtotal venta</TableHead>
              <TableHead>Margen</TableHead>
            </TableRow>
          </TableHeader>

          <TableBody>
            {items.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={7}
                  className="py-8 text-center text-sm text-muted-foreground"
                >
                  No hay ítems para mostrar.
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.product_id}</TableCell>
                  <TableCell>{item.quantity}</TableCell>
                  <TableCell>{formatMoney(item.unit_cost)}</TableCell>
                  <TableCell>{formatMoney(item.unit_price)}</TableCell>
                  <TableCell>{formatMoney(item.subtotal_cost)}</TableCell>
                  <TableCell>{formatMoney(item.subtotal)}</TableCell>
                  <TableCell>{formatMoney(item.margin_amount)}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}