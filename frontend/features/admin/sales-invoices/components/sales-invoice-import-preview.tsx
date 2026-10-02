"use client";

import { Fragment } from "react";
import type { SalesInvoiceImportPreviewResponse } from "@/features/admin/sales-invoices/types";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type SalesInvoiceImportPreviewProps = {
  preview: SalesInvoiceImportPreviewResponse | null;
};

function formatMoney(value: string | null) {
  const numericValue = Number(value ?? 0);

  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 2,
  }).format(Number.isNaN(numericValue) ? 0 : numericValue);
}

export function SalesInvoiceImportPreview({ preview }: SalesInvoiceImportPreviewProps) {
  if (!preview) return null;

  return (
    <div className="space-y-4 rounded-xl border p-4">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-lg border p-3">
          <p className="text-xs text-muted-foreground">Cliente</p>
          <p className="break-words font-medium">{preview.client_name ?? "-"}</p>
        </div>
        <div className="rounded-lg border p-3">
          <p className="text-xs text-muted-foreground">Número</p>
          <p className="break-words font-medium">{preview.invoice_number ?? "-"}</p>
        </div>
        <div className="rounded-lg border p-3">
          <p className="text-xs text-muted-foreground">Fecha</p>
          <p className="font-medium">{preview.invoice_date ?? "-"}</p>
        </div>
        <div className="rounded-lg border p-3">
          <p className="text-xs text-muted-foreground">Total detectado</p>
          <p className="font-medium">{formatMoney(preview.total_amount)}</p>
        </div>
      </div>

      {preview.warnings.length > 0 && (
        <div className="rounded-lg border border-kraft/20 bg-kraft/10 p-3 text-sm text-kraft">
          <p className="mb-2 font-medium">Advertencias</p>
          <div className="space-y-1">
            {preview.warnings.map((warning, index) => (
              <p key={index}>{warning}</p>
            ))}
          </div>
        </div>
      )}

      {preview.errors.length > 0 && (
        <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
          <p className="mb-2 font-medium">Errores detectados</p>
          <div className="space-y-1">
            {preview.errors.map((error, index) => (
              <p key={index}>{error}</p>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-3">
        <h3 className="text-sm font-semibold">Ítems detectados</h3>

        {preview.items.length === 0 ? (
          <div className="rounded-xl border px-4 py-8 text-center text-sm text-muted-foreground">
            No se detectaron ítems.
          </div>
        ) : (
          <Fragment>
            <div className="space-y-3 md:hidden">
              {preview.items.map((item, index) => (
                <div key={index} className="space-y-3 rounded-xl border p-4">
                  <div>
                    <p className="font-medium">{item.product_name ?? "-"}</p>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-xs text-muted-foreground">Cantidad</p>
                      <p className="font-medium">{item.quantity ?? "-"}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Confianza</p>
                      <p className="font-medium">
                        {item.confidence != null ? `${Math.round(item.confidence * 100)}%` : "-"}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Costo unitario</p>
                      <p className="font-medium">{formatMoney(item.unit_cost)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Precio unitario</p>
                      <p className="font-medium">{formatMoney(item.unit_price)}</p>
                    </div>
                    <div className="col-span-2">
                      <p className="text-xs text-muted-foreground">Subtotal</p>
                      <p className="font-medium">{formatMoney(item.subtotal)}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="hidden overflow-hidden rounded-xl border md:block">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Producto</TableHead>
                      <TableHead>Cantidad</TableHead>
                      <TableHead>Costo unitario</TableHead>
                      <TableHead>Precio unitario</TableHead>
                      <TableHead>Subtotal</TableHead>
                      <TableHead>Confianza</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {preview.items.map((item, index) => (
                      <TableRow key={index}>
                        <TableCell>{item.product_name ?? "-"}</TableCell>
                        <TableCell>{item.quantity ?? "-"}</TableCell>
                        <TableCell>{formatMoney(item.unit_cost)}</TableCell>
                        <TableCell>{formatMoney(item.unit_price)}</TableCell>
                        <TableCell>{formatMoney(item.subtotal)}</TableCell>
                        <TableCell>
                          {item.confidence != null ? `${Math.round(item.confidence * 100)}%` : "-"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          </Fragment>
        )}
      </div>
    </div>
  );
}