"use client";

import { useState, Fragment } from "react";
import { toast } from "sonner";
import { FileSpreadsheet, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useImportClientSales } from "@/features/admin/account-ledger/hooks/use-import-client-sales";
import {
  DocumentTypeBadge,
  formatCurrency,
} from "@/features/admin/account-ledger/components/ledger-helpers";
import type { ClientImportResult } from "@/features/admin/account-ledger/types";

export function ImportClientSalesCard() {
  const importMutation = useImportClientSales();

  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ClientImportResult | null>(null);

  async function handlePreview() {
    if (!file) return;
    try {
      const result = await importMutation.mutateAsync({ file, dryRun: true });
      setPreview(result);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "No se pudo analizar el archivo");
    }
  }

  async function handleConfirm() {
    if (!file) return;
    try {
      const result = await importMutation.mutateAsync({ file, dryRun: false });
      const totalUnassigned = result.payments_applied.reduce(
        (acc, p) => acc + Number(p.unassigned_amount),
        0
      );
      const paymentsMsg =
        result.payments_applied.length > 0
          ? ` y ${result.payments_applied.length} cobro(s) aplicados${
              totalUnassigned > 0 ? " (con saldo sin asignar, revisar abajo)" : ""
            }`
          : "";
      const invoicesCreated = result.created_sales_invoice_ids.length;
      const quotesCreated = result.created_sales_quote_ids.length;
      const createdParts = [
        invoicesCreated > 0
          ? `${invoicesCreated} remito${invoicesCreated === 1 ? "" : "s"}`
          : null,
        quotesCreated > 0
          ? `${quotesCreated} presupuesto${quotesCreated === 1 ? "" : "s"}`
          : null,
      ].filter(Boolean);

      if (createdParts.length > 0) {
        toast.success(`Se crearon ${createdParts.join(" y ")}${paymentsMsg}`);
      } else if (result.rows_skipped_already_imported > 0) {
        toast.info(
          `No había ventas nuevas: ${result.rows_skipped_already_imported} fila(s) ya estaban importadas${paymentsMsg}`
        );
      } else {
        toast.info(`No se creó ningún documento${paymentsMsg}`);
      }
      setPreview(result);
      setFile(null);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "No se pudo importar");
    }
  }

  const invoiceRowsCount =
    preview?.rows_to_import.filter((row) => row.document_type === "sales_invoice").length ?? 0;
  const quoteRowsCount =
    preview?.rows_to_import.filter((row) => row.document_type === "sales_quote").length ?? 0;

  return (
    <div className="space-y-4 rounded-2xl border bg-background p-4 shadow-sm sm:p-6">
      <div className="flex items-start gap-3">
        <div className="rounded-xl border bg-muted/40 p-2">
          <FileSpreadsheet className="h-4 w-4" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-semibold">Importar ventas a clientes</h3>
          <p className="text-sm text-muted-foreground">
            Subí el Excel completo: las pestañas de cada vendedor (producto, cantidad, cliente)
            se usan para generar las ventas con detalle real de producto, y la hoja &quot;Registro
            Clientes&quot; se usa como cuenta corriente para aplicar los pagos ya cobrados.
          </p>
          <p className="text-xs text-muted-foreground">
            El cliente y el producto tienen que existir ya en el sistema (se matchean por
            nombre). Los pagos de &quot;Registro Clientes&quot; se asignan a las ventas más antiguas
            primero (FIFO).
          </p>
          <p className="text-xs text-muted-foreground">
            Opcional: agregá una columna <span className="font-medium">document</span> en las
            pestañas de vendedores con <span className="font-medium">remito</span> (invoice) o{" "}
            <span className="font-medium">presupuesto</span> (quote) para elegir el tipo de cada
            fila. Si queda vacía, la fila se importa como remito.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <div className="space-y-1.5">
          <Label className="text-xs">Archivo Excel</Label>
          <Input
            type="file"
            accept=".xlsx,.xls"
            onChange={(e) => {
              setFile(e.target.files?.[0] ?? null);
              setPreview(null);
            }}
          />
        </div>

        <Button type="button" onClick={handlePreview} disabled={!file || importMutation.isPending}>
          <Upload className="mr-2 h-4 w-4" />
          {importMutation.isPending ? "Analizando..." : "Previsualizar"}
        </Button>
      </div>

      {preview && (
        <div className="space-y-4 rounded-xl border p-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Filas leídas</p>
              <p className="text-xl font-semibold">{preview.total_rows_read}</p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Ventas a importar</p>
              <p className="text-xl font-semibold">{preview.rows_to_import.length}</p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Con errores</p>
              <p className="text-xl font-semibold">{preview.rows_with_errors.length}</p>
            </div>
          </div>

          <p className="text-sm text-muted-foreground">
            {invoiceRowsCount} fila{invoiceRowsCount === 1 ? "" : "s"} de remito ·{" "}
            {quoteRowsCount} fila{quoteRowsCount === 1 ? "" : "s"} de presupuesto
          </p>

          {quoteRowsCount > 0 && (
            <p className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-2.5 text-xs">
              Los presupuestos importados quedan aprobados y registran deuda en la cuenta
              corriente del cliente, pero no descuentan stock.
            </p>
          )}

          {preview.rows_with_errors.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold">Filas con errores (se omiten)</h4>

              {/* Vista mobile: cards */}
              <div className="max-h-48 space-y-2 overflow-y-auto md:hidden">
                {preview.rows_with_errors.map((row, index) => (
                  <div
                    key={`${row.row_number}-${index}`}
                    className="rounded-lg border p-3 text-sm"
                  >
                    <p className="text-xs text-muted-foreground">Fila {row.row_number}</p>
                    <p className="text-destructive">{row.errors.join(", ")}</p>
                  </div>
                ))}
              </div>

              {/* Vista desktop: tabla */}
              <div className="hidden max-h-48 overflow-y-auto overflow-x-auto rounded-lg border md:block">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Fila</TableHead>
                      <TableHead>Errores</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {preview.rows_with_errors.map((row, index) => (
                      <TableRow key={`${row.row_number}-${index}`}>
                        <TableCell>{row.row_number}</TableCell>
                        <TableCell className="text-destructive">
                          {row.errors.join(", ")}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}

          {preview.rows_to_import.length > 0 && (
            <Fragment>
              {/* Vista mobile: cards */}
              <div className="max-h-64 space-y-2 overflow-y-auto md:hidden">
                {preview.rows_to_import.map((row, index) => (
                  <div
                    key={`${row.row_number}-${row.product_name}-${index}`}
                    className="space-y-2 rounded-lg border p-3 text-sm"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <p className="font-medium">{row.product_name}</p>
                      <DocumentTypeBadge documentType={row.document_type} />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {row.client_name} · {row.sales_rep_name ?? "—"} · {row.sale_date}
                    </p>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Cant. {row.quantity}</span>
                      <span className="font-medium">{formatCurrency(row.amount)}</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Vista desktop: tabla */}
              <div className="hidden max-h-64 overflow-y-auto overflow-x-auto rounded-lg border md:block">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Documento</TableHead>
                      <TableHead>Vendedor</TableHead>
                      <TableHead>Cliente</TableHead>
                      <TableHead>Producto</TableHead>
                      <TableHead className="text-right">Cantidad</TableHead>
                      <TableHead className="text-right">Importe</TableHead>
                      <TableHead>Fecha</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {preview.rows_to_import.map((row, index) => (
                      <TableRow key={`${row.row_number}-${row.product_name}-${index}`}>
                        <TableCell>
                          <DocumentTypeBadge documentType={row.document_type} />
                        </TableCell>
                        <TableCell>{row.sales_rep_name ?? "—"}</TableCell>
                        <TableCell>{row.client_name}</TableCell>
                        <TableCell>{row.product_name}</TableCell>
                        <TableCell className="text-right">{row.quantity}</TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(row.amount)}
                        </TableCell>
                        <TableCell>{row.sale_date}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </Fragment>
          )}

          {preview.payments_applied.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold">Cobros aplicados (Registro Clientes)</h4>

              {/* Vista mobile: cards */}
              <div className="max-h-48 space-y-2 overflow-y-auto md:hidden">
                {preview.payments_applied.map((payment, index) => (
                  <div
                    key={`${payment.row_number}-${index}`}
                    className="space-y-2 rounded-lg border p-3 text-sm"
                  >
                    <p className="font-medium">{payment.client_name}</p>
                    <div className="grid grid-cols-3 gap-2">
                      <div>
                        <p className="text-xs text-muted-foreground">Cobrado</p>
                        <p>{formatCurrency(payment.amount)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Asignado</p>
                        <p>{formatCurrency(payment.allocated_amount)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Sin asignar</p>
                        {Number(payment.unassigned_amount) > 0 ? (
                          <p className="text-amber-600">
                            {formatCurrency(payment.unassigned_amount)}
                          </p>
                        ) : (
                          <p>-</p>
                        )}
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Remitos:{" "}
                      {payment.invoice_numbers.length > 0
                        ? payment.invoice_numbers.join(", ")
                        : "-"}
                    </p>
                  </div>
                ))}
              </div>

              {/* Vista desktop: tabla */}
              <div className="hidden max-h-48 overflow-y-auto overflow-x-auto rounded-lg border md:block">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Cliente</TableHead>
                      <TableHead className="text-right">Cobrado</TableHead>
                      <TableHead className="text-right">Asignado</TableHead>
                      <TableHead className="text-right">Sin asignar</TableHead>
                      <TableHead>Remitos</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {preview.payments_applied.map((payment, index) => (
                      <TableRow key={`${payment.row_number}-${index}`}>
                        <TableCell>{payment.client_name}</TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(payment.amount)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(payment.allocated_amount)}
                        </TableCell>
                        <TableCell className="text-right">
                          {Number(payment.unassigned_amount) > 0 ? (
                            <span className="text-amber-600">
                              {formatCurrency(payment.unassigned_amount)}
                            </span>
                          ) : (
                            "-"
                          )}
                        </TableCell>
                        <TableCell className="whitespace-nowrap">
                          {payment.invoice_numbers.length > 0
                            ? payment.invoice_numbers.join(", ")
                            : "-"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}

          {!preview.dry_run ? (
            <p className="text-sm text-brand">
              Importación completada:{" "}
              {preview.created_sales_invoice_ids.length} remito
              {preview.created_sales_invoice_ids.length === 1 ? "" : "s"} y{" "}
              {preview.created_sales_quote_ids.length} presupuesto
              {preview.created_sales_quote_ids.length === 1 ? "" : "s"} creados
              {preview.rows_skipped_already_imported > 0
                ? ` (${preview.rows_skipped_already_imported} fila(s) omitidas por estar ya importadas)`
                : ""}
              .
            </p>
          ) : (
            <div className="flex justify-end">
              <Button
                type="button"
                onClick={handleConfirm}
                disabled={preview.rows_to_import.length === 0 || importMutation.isPending}
              >
                {importMutation.isPending ? "Importando..." : "Confirmar importación"}
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}