"use client";

import type { PurchaseQuote } from "@/features/admin/purchase-quotes/types";
import { DownloadPurchaseQuoteButton } from "@/features/admin/purchase-quotes/components/download-purchase-quote-button";
import { PurchaseQuoteStatusBadge } from "@/features/admin/purchase-quotes/components/purchase-quote-status-badge";
import { UpdatePurchaseQuoteStatusSelect } from "@/features/admin/purchase-quotes/components/update-purchase-quote-status-select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type PurchaseQuotesTableProps = {
  purchaseQuotes: PurchaseQuote[];
};

function formatMoney(value: string | null) {
  const numericValue = Number(value ?? 0);
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 2,
  }).format(Number.isNaN(numericValue) ? 0 : numericValue);
}

function formatDate(value: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("es-AR").format(date);
}

export function PurchaseQuotesTable({ purchaseQuotes }: PurchaseQuotesTableProps) {
  if (purchaseQuotes.length === 0) {
    return (
      <div className="rounded-2xl border bg-background p-8 text-center text-sm text-muted-foreground shadow-sm">
        No hay presupuestos de compra para mostrar.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Cards para Mobile */}
      <div className="grid gap-3 md:hidden">
        {purchaseQuotes.map((quote) => (
          <div key={quote.id} className="rounded-2xl border bg-background p-4 shadow-sm space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 space-y-0.5">
                <p className="text-sm font-bold">#{quote.id}</p>
                <p className="truncate text-sm font-semibold text-foreground">
                  {quote.supplier_name}
                </p>
              </div>
              <PurchaseQuoteStatusBadge status={quote.status} />
            </div>

            <div className="grid grid-cols-2 gap-2 rounded-xl border bg-muted/20 p-2.5 text-xs">
              <div>
                <p className="text-muted-foreground">Número</p>
                <p className="font-medium font-mono truncate">{quote.quote_number}</p>
              </div>
              <div>
                <p className="text-muted-foreground text-right">Total</p>
                <p className="font-bold text-right text-foreground">
                  {formatMoney(quote.total_amount)}
                </p>
              </div>
            </div>

            <div className="pt-1 flex items-center gap-2">
              <UpdatePurchaseQuoteStatusSelect purchaseQuote={quote} />
              <DownloadPurchaseQuoteButton purchaseQuote={quote} />
            </div>
          </div>
        ))}
      </div>

      {/* Tabla para Desktop */}
      <div className="hidden overflow-hidden rounded-2xl border bg-background shadow-sm md:block">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[60px]">ID</TableHead>
                <TableHead>Proveedor</TableHead>
                <TableHead>Número</TableHead>
                <TableHead>Fecha</TableHead>
                <TableHead>Válido hasta</TableHead>
                <TableHead className="text-right">Total</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead className="text-center w-[60px]">Items</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {purchaseQuotes.map((quote) => (
                <TableRow key={quote.id}>
                  <TableCell className="font-medium">#{quote.id}</TableCell>
                  <TableCell className="min-w-[180px] max-w-[220px] truncate font-semibold">
                    {quote.supplier_name}
                  </TableCell>
                  <TableCell className="font-mono text-sm">{quote.quote_number}</TableCell>
                  <TableCell>{formatDate(quote.quote_date)}</TableCell>
                  <TableCell>{formatDate(quote.valid_until)}</TableCell>
                  <TableCell className="text-right font-medium">
                    {formatMoney(quote.total_amount)}
                  </TableCell>
                  <TableCell>
                    <PurchaseQuoteStatusBadge status={quote.status} />
                  </TableCell>
                  <TableCell className="text-center">{quote.items.length}</TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-2">
                      <UpdatePurchaseQuoteStatusSelect purchaseQuote={quote} />
                      <DownloadPurchaseQuoteButton purchaseQuote={quote} />
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}
