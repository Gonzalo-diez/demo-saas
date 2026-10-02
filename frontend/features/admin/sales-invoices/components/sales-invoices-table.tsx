"use client";

import type { SalesInvoice } from "@/features/admin/sales-invoices/types";
import { DownloadSalesInvoiceButton } from "@/features/admin/sales-invoices/components/download-sales-invoice-button";
import { SalesInvoiceStatusBadge } from "@/features/admin/sales-invoices/components/sales-invoice-status-badge";
import { UpdateSalesInvoiceStatusSelect } from "@/features/admin/sales-invoices/components/update-sales-invoice-status-select";
import { DocumentPendingChecksBadge } from "@/features/admin/checks/components/document-pending-checks-badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

type SalesInvoicesTableProps = {
  salesInvoices: SalesInvoice[];
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
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("es-AR").format(date);
}

function SalesTypeBadge({ salesType }: { salesType: string | null }) {
  if (!salesType) return <span className="text-muted-foreground">-</span>;
  return (
    <Badge
      variant={salesType === "B2B" ? "outline" : "secondary"}
      className="whitespace-nowrap font-medium"
    >
      {salesType}
    </Badge>
  );
}

export function SalesInvoicesTable({ salesInvoices }: SalesInvoicesTableProps) {
  if (salesInvoices.length === 0) {
    return (
      <div className="rounded-2xl border bg-background p-8 text-center text-sm text-muted-foreground shadow-sm">
        No hay facturas de venta para mostrar.
      </div>
    );
  }

  const b2bInvoices = salesInvoices.filter((inv) => inv.sales_type === "B2B");
  const onlineInvoices = salesInvoices.filter(
    (inv) => inv.sales_type === "ONLINE",
  );

  return (
    <Tabs defaultValue="all" className="w-full space-y-4">
      <div className="flex items-center justify-between">
        {/* Tabs amigables para pantallas móviles */}
        <TabsList className="w-full md:w-auto grid grid-cols-3 md:inline-flex">
          <TabsTrigger value="all">Todos ({salesInvoices.length})</TabsTrigger>
          <TabsTrigger value="b2b">B2B ({b2bInvoices.length})</TabsTrigger>
          <TabsTrigger value="online">
            Online ({onlineInvoices.length})
          </TabsTrigger>
        </TabsList>
      </div>

      <TabsContent value="all" className="border-none p-0 outline-none">
        <AllTableContent invoices={salesInvoices} />
      </TabsContent>

      <TabsContent value="b2b" className="border-none p-0 outline-none">
        <B2BTableContent invoices={b2bInvoices} />
      </TabsContent>

      <TabsContent value="online" className="border-none p-0 outline-none">
        <OnlineTableContent invoices={onlineInvoices} />
      </TabsContent>
    </Tabs>
  );
}

// --- CONTENIDO TODOS (Móvil e Desktop) ---
function AllTableContent({ invoices }: { invoices: SalesInvoice[] }) {
  if (invoices.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed p-8 text-center text-sm text-muted-foreground">
        No hay remitos de venta para mostrar.
      </div>
    );
  }

  function customerLabel(inv: SalesInvoice) {
    if (inv.sales_type === "B2B") {
      return inv.client?.name ?? `Cliente #${inv.client_id}`;
    }
    return inv.customer_name ?? "Cliente Web Ocasional";
  }

  function customerSublabel(inv: SalesInvoice) {
    if (inv.sales_type === "B2B") {
      return inv.client_branch?.name ?? "Sin sucursal";
    }
    return inv.order_id ? `Orden #${inv.order_id}` : (inv.customer_email ?? inv.customer_phone ?? "-");
  }

  return (
    <div className="space-y-4">
      {/* Cards para Mobile */}
      <div className="grid gap-3 md:hidden">
        {invoices.map((inv) => (
          <div
            key={inv.id}
            className="rounded-2xl border bg-background p-4 shadow-sm space-y-3"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 space-y-0.5">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-bold">#{inv.id}</p>
                  <SalesTypeBadge salesType={inv.sales_type} />
                </div>
                <p className="truncate text-sm font-semibold text-foreground">
                  {customerLabel(inv)}
                </p>
                <p className="text-xs text-muted-foreground truncate">
                  {customerSublabel(inv)}
                </p>
              </div>
              <SalesInvoiceStatusBadge status={inv.status} />
            </div>

            <div className="grid grid-cols-2 gap-2 rounded-xl border bg-muted/20 p-2.5 text-xs">
              <div>
                <p className="text-muted-foreground">Número</p>
                <p className="font-medium font-mono truncate">
                  {inv.invoice_number}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground text-right">Total</p>
                <p className="font-bold text-right text-foreground">
                  {formatMoney(inv.total_amount)}
                </p>
              </div>
            </div>

            <DocumentPendingChecksBadge documentType="sales_invoice" documentId={inv.id} />

            <div className="pt-1">
              <UpdateSalesInvoiceStatusSelect salesInvoice={inv} />
              <DownloadSalesInvoiceButton salesInvoice={inv} />
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
                <TableHead>Tipo</TableHead>
                <TableHead>Cliente / Comprador</TableHead>
                <TableHead>Número</TableHead>
                <TableHead>Fecha</TableHead>
                <TableHead className="text-right">Total</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead className="text-center w-[60px]">Items</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {invoices.map((inv) => (
                <TableRow key={inv.id}>
                  <TableCell className="font-medium">#{inv.id}</TableCell>
                  <TableCell>
                    <SalesTypeBadge salesType={inv.sales_type} />
                  </TableCell>
                  <TableCell className="min-w-[180px] max-w-[220px]">
                    <p className="truncate font-semibold">{customerLabel(inv)}</p>
                    <p className="truncate text-xs text-muted-foreground">
                      {customerSublabel(inv)}
                    </p>
                  </TableCell>
                  <TableCell className="font-mono text-sm">
                    {inv.invoice_number}
                  </TableCell>
                  <TableCell>{formatDate(inv.invoice_date)}</TableCell>
                  <TableCell className="text-right font-medium">
                    {formatMoney(inv.total_amount)}
                  </TableCell>
                  <TableCell>
                    <SalesInvoiceStatusBadge status={inv.status} />
                  </TableCell>
                  <TableCell className="text-center">
                    {inv.items.length}
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-col items-end gap-1.5">
                      <DocumentPendingChecksBadge
                        documentType="sales_invoice"
                        documentId={inv.id}
                      />
                      <div className="flex justify-end">
                        <UpdateSalesInvoiceStatusSelect salesInvoice={inv} />
                        <DownloadSalesInvoiceButton salesInvoice={inv} />
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

// --- CONTENIDO B2B (Móvil e Desktop) ---
function B2BTableContent({ invoices }: { invoices: SalesInvoice[] }) {
  if (invoices.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed p-8 text-center text-sm text-muted-foreground">
        No hay facturas B2B para mostrar.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Cards para Mobile */}
      <div className="grid gap-3 md:hidden">
        {invoices.map((inv) => (
          <div
            key={inv.id}
            className="rounded-2xl border bg-background p-4 shadow-sm space-y-3"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 space-y-0.5">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-bold">#{inv.id}</p>
                  <SalesTypeBadge salesType={inv.sales_type} />
                </div>
                <p className="truncate text-sm font-semibold text-foreground">
                  {inv.client?.name ?? `Cliente #${inv.client_id}`}
                </p>
                <p className="text-xs text-muted-foreground truncate">
                  {inv.client_branch?.name ?? "Sin sucursal"}
                </p>
              </div>
              <SalesInvoiceStatusBadge status={inv.status} />
            </div>

            <div className="grid grid-cols-2 gap-2 rounded-xl border bg-muted/20 p-2.5 text-xs">
              <div>
                <p className="text-muted-foreground">Nro Factura</p>
                <p className="font-medium font-mono truncate">
                  {inv.invoice_number}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground text-right">Total</p>
                <p className="font-bold text-right text-foreground">
                  {formatMoney(inv.total_amount)}
                </p>
              </div>
            </div>

            <div className="pt-1">
              <UpdateSalesInvoiceStatusSelect salesInvoice={inv} />
              <DownloadSalesInvoiceButton salesInvoice={inv} />
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
                <TableHead>Cliente Corporativo</TableHead>
                <TableHead>Sucursal</TableHead>
                <TableHead>Número</TableHead>
                <TableHead>Fecha</TableHead>
                <TableHead className="text-right">Total</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead className="text-center w-[60px]">Items</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {invoices.map((inv) => (
                <TableRow key={inv.id}>
                  <TableCell className="font-medium">#{inv.id}</TableCell>
                  <TableCell className="min-w-[180px] max-w-[220px] truncate font-semibold">
                    {inv.client?.name ?? `Cliente #${inv.client_id}`}
                  </TableCell>
                  <TableCell className="max-w-[160px] truncate text-muted-foreground">
                    {inv.client_branch?.name ?? "-"}
                  </TableCell>
                  <TableCell className="font-mono text-sm">
                    {inv.invoice_number}
                  </TableCell>
                  <TableCell>{formatDate(inv.invoice_date)}</TableCell>
                  <TableCell className="text-right font-medium">
                    {formatMoney(inv.total_amount)}
                  </TableCell>
                  <TableCell>
                    <SalesInvoiceStatusBadge status={inv.status} />
                  </TableCell>
                  <TableCell className="text-center">
                    {inv.items.length}
                  </TableCell>
                  <TableCell>
                    <div className="flex justify-end">
                      <UpdateSalesInvoiceStatusSelect salesInvoice={inv} />
                      <DownloadSalesInvoiceButton salesInvoice={inv} />
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

// --- CONTENIDO ONLINE (Móvil e Desktop) ---
function OnlineTableContent({ invoices }: { invoices: SalesInvoice[] }) {
  if (invoices.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed p-8 text-center text-sm text-muted-foreground">
        No hay facturas online para mostrar.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Cards para Mobile */}
      <div className="grid gap-3 md:hidden">
        {invoices.map((inv) => (
          <div
            key={inv.id}
            className="rounded-2xl border bg-background p-4 shadow-sm space-y-3"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 space-y-0.5">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-bold">#{inv.id}</p>
                  <SalesTypeBadge salesType={inv.sales_type} />
                </div>
                <p className="truncate text-sm font-semibold text-foreground">
                  {inv.customer_name ?? "Cliente Web Ocasional"}
                </p>
                {inv.order_id && (
                  <p className="text-xs text-muted-foreground">
                    Orden: #{inv.order_id}
                  </p>
                )}
              </div>
              <SalesInvoiceStatusBadge status={inv.status} />
            </div>

            {(inv.customer_email || inv.customer_phone) && (
              <div className="rounded-xl border bg-muted/10 p-2.5 text-xs text-muted-foreground space-y-0.5">
                {inv.customer_email && (
                  <p className="truncate">
                    <b className="text-foreground">Email:</b>{" "}
                    {inv.customer_email}
                  </p>
                )}
                {inv.customer_phone && (
                  <p>
                    <b className="text-foreground">Tel:</b> {inv.customer_phone}
                  </p>
                )}
              </div>
            )}

            <div className="grid grid-cols-2 gap-2 rounded-xl border bg-muted/20 p-2.5 text-xs">
              <div>
                <p className="text-muted-foreground">Nro Factura</p>
                <p className="font-medium font-mono truncate">
                  {inv.invoice_number}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground text-right">Total</p>
                <p className="font-bold text-right text-foreground">
                  {formatMoney(inv.total_amount)}
                </p>
              </div>
            </div>

            <div className="pt-1">
              <UpdateSalesInvoiceStatusSelect salesInvoice={inv} />
              <DownloadSalesInvoiceButton salesInvoice={inv} />
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
                <TableHead>Orden</TableHead>
                <TableHead>Comprador / Cliente Online</TableHead>
                <TableHead>Contacto</TableHead>
                <TableHead>Número Remito</TableHead>
                <TableHead>Fecha</TableHead>
                <TableHead className="text-right">Total</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead className="text-center w-[60px]">Items</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {invoices.map((inv) => (
                <TableRow key={inv.id}>
                  <TableCell className="font-medium">#{inv.id}</TableCell>
                  <TableCell>
                    {inv.order_id ? `#${inv.order_id}` : "-"}
                  </TableCell>
                  <TableCell className="min-w-[160px] font-medium">
                    {inv.customer_name ?? (
                      <span className="text-muted-foreground italic">
                        No especificado
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="min-w-[180px]">
                    <div className="text-xs space-y-0.5 text-muted-foreground">
                      {inv.customer_email && (
                        <p className="truncate max-w-[200px] text-foreground">
                          {inv.customer_email}
                        </p>
                      )}
                      {inv.customer_phone && <p>{inv.customer_phone}</p>}
                    </div>
                  </TableCell>
                  <TableCell className="font-mono text-sm">
                    {inv.invoice_number}
                  </TableCell>
                  <TableCell>{formatDate(inv.invoice_date)}</TableCell>
                  <TableCell className="text-right font-medium">
                    {formatMoney(inv.total_amount)}
                  </TableCell>
                  <TableCell>
                    <SalesInvoiceStatusBadge status={inv.status} />
                  </TableCell>
                  <TableCell className="text-center">
                    {inv.items.length}
                  </TableCell>
                  <TableCell>
                    <div className="flex justify-end">
                      <UpdateSalesInvoiceStatusSelect salesInvoice={inv} />
                      <DownloadSalesInvoiceButton salesInvoice={inv} />
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