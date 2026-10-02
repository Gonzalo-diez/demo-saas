"use client";

import type { PurchaseInvoice } from "@/features/admin/purchase-invoices/types";
import { DownloadPurchaseInvoiceButton } from "@/features/admin/purchase-invoices/components/download-purchase-invoice-button";
import { PurchaseInvoiceStatusBadge } from "@/features/admin/purchase-invoices/components/purchase-invoice-status-badge";
import { UpdatePurchaseInvoiceStatusSelect } from "@/features/admin/purchase-invoices/components/update-purchase-invoice-status-select";
import { DocumentPendingChecksBadge } from "@/features/admin/checks/components/document-pending-checks-badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type PurchaseInvoicesTableProps = {
  purchaseInvoices: PurchaseInvoice[];
};

function formatMoney(value: string | null) {
  const numericValue = Number(value ?? 0);

  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 2,
  }).format(Number.isNaN(numericValue) ? 0 : numericValue);
}

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("es-AR").format(date);
}

export function PurchaseInvoicesTable({
  purchaseInvoices,
}: PurchaseInvoicesTableProps) {
  if (purchaseInvoices.length === 0) {
    return (
      <div className="rounded-2xl border bg-background p-8 text-center text-sm text-muted-foreground shadow-sm">
        No hay facturas de compra para mostrar.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-3 md:hidden">
        {purchaseInvoices.map((purchaseInvoice) => (
          <div
            key={purchaseInvoice.id}
            className="rounded-2xl border bg-background p-4 shadow-sm"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 space-y-1">
                <p className="text-sm font-semibold">#{purchaseInvoice.id}</p>
                <p className="truncate text-sm font-medium">
                  {purchaseInvoice.supplier_name || "Sin proveedor"}
                </p>
                <p className="text-xs text-muted-foreground">
                  {purchaseInvoice.supplier_tax_id || "-"}
                </p>
              </div>

              <PurchaseInvoiceStatusBadge status={purchaseInvoice.status} />
            </div>

            <div className="mt-4 grid gap-3 rounded-xl border bg-muted/20 p-3 text-sm sm:grid-cols-2">
              <div>
                <p className="text-xs text-muted-foreground">Número</p>
                <p className="font-medium">{purchaseInvoice.invoice_number}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Fecha</p>
                <p className="font-medium">
                  {formatDate(purchaseInvoice.invoice_date)}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Total</p>
                <p className="font-medium">
                  {formatMoney(purchaseInvoice.total_amount)}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Items</p>
                <p className="font-medium">{purchaseInvoice.items.length}</p>
              </div>
            </div>

            <div className="mt-3">
              <DocumentPendingChecksBadge
                documentType="purchase_invoice"
                documentId={purchaseInvoice.id}
              />
            </div>

            <div className="mt-4">
              <UpdatePurchaseInvoiceStatusSelect
                purchaseInvoice={purchaseInvoice}
              />
              <DownloadPurchaseInvoiceButton
                purchaseInvoice={purchaseInvoice}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="hidden overflow-hidden rounded-2xl border bg-background shadow-sm md:block">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Proveedor</TableHead>
                <TableHead>Número</TableHead>
                <TableHead>Fecha</TableHead>
                <TableHead>Total</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Items</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {purchaseInvoices.map((purchaseInvoice) => (
                <TableRow key={purchaseInvoice.id}>
                  <TableCell className="font-medium">
                    #{purchaseInvoice.id}
                  </TableCell>
                  <TableCell className="min-w-[220px]">
                    <div className="space-y-1">
                      <p className="font-medium">
                        {purchaseInvoice.supplier_name || "Sin proveedor"}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {purchaseInvoice.supplier_tax_id || "-"}
                      </p>
                    </div>
                  </TableCell>
                  <TableCell>{purchaseInvoice.invoice_number}</TableCell>
                  <TableCell>
                    {formatDate(purchaseInvoice.invoice_date)}
                  </TableCell>
                  <TableCell>
                    {formatMoney(purchaseInvoice.total_amount)}
                  </TableCell>
                  <TableCell>
                    <PurchaseInvoiceStatusBadge
                      status={purchaseInvoice.status}
                    />
                  </TableCell>
                  <TableCell>{purchaseInvoice.items.length}</TableCell>
                  <TableCell>
                    <div className="flex flex-col items-end gap-1.5">
                      <DocumentPendingChecksBadge
                        documentType="purchase_invoice"
                        documentId={purchaseInvoice.id}
                      />
                      <div className="flex justify-end">
                        <UpdatePurchaseInvoiceStatusSelect
                          purchaseInvoice={purchaseInvoice}
                        />
                        <DownloadPurchaseInvoiceButton
                          purchaseInvoice={purchaseInvoice}
                        />
                      </div>
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