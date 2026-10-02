"use client";

import { useState, Fragment } from "react";
import { toast } from "sonner";
import { FileSpreadsheet, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useSalesReps } from "@/features/admin/sales-reps/hooks/use-sales-reps";
import { useSuppliers } from "@/features/admin/suppliers/hooks/use-suppliers";
import { useImportSupplierPurchases } from "@/features/admin/account-ledger/hooks/use-import-supplier-purchases";
import {
  DocumentTypeBadge,
  formatCurrency,
} from "@/features/admin/account-ledger/components/ledger-helpers";
import type { SupplierImportResult } from "@/features/admin/account-ledger/types";

export function ImportSupplierPurchasesCard() {
  const { data: salesRepsData } = useSalesReps({ page: 1, page_size: 20, status: "active" });
  const { data: suppliersData } = useSuppliers({ page: 1, page_size: 20, status: "active" });
  const importMutation = useImportSupplierPurchases();

  const [file, setFile] = useState<File | null>(null);
  const [salesRepId, setSalesRepId] = useState<string>("");
  const [supplierId, setSupplierId] = useState<string>("");
  const [purchaseDate, setPurchaseDate] = useState<string>(
    new Date().toISOString().slice(0, 10)
  );
  const [preview, setPreview] = useState<SupplierImportResult | null>(null);

  const canPreview = Boolean(file && salesRepId && supplierId && purchaseDate);

  const invoiceRowsCount =
    preview?.rows_to_import.filter((row) => row.document_type === "purchase_invoice").length ?? 0;
  const quoteRowsCount =
    preview?.rows_to_import.filter((row) => row.document_type === "purchase_quote").length ?? 0;

  async function handlePreview() {
    if (!file || !salesRepId || !supplierId) return;
    try {
      const result = await importMutation.mutateAsync({
        file,
        salesRepId: Number(salesRepId),
        supplierId: Number(supplierId),
        purchaseDate,
        dryRun: true,
      });
      setPreview(result);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "No se pudo analizar el archivo");
    }
  }

  async function handleConfirm() {
    if (!file || !salesRepId || !supplierId) return;
    try {
      const result = await importMutation.mutateAsync({
        file,
        salesRepId: Number(salesRepId),
        supplierId: Number(supplierId),
        purchaseDate,
        dryRun: false,
      });
      const createdParts = [
        result.purchase_invoice_id ? "remito de compra" : null,
        result.purchase_quote_id ? "presupuesto de compra" : null,
      ].filter(Boolean);
      toast.success(
        createdParts.length > 0
          ? `Se creó: ${createdParts.join(" y ")}`
          : "No se creó ningún documento"
      );
      setPreview(result);
      setFile(null);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "No se pudo importar la compra");
    }
  }

  return (
    <div className="space-y-4 rounded-2xl border bg-background p-4 shadow-sm sm:p-6">
      <div className="flex items-start gap-3">
        <div className="rounded-xl border bg-muted/40 p-2">
          <FileSpreadsheet className="h-4 w-4" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-semibold">Importar pedido desde Excel</h3>
          <p className="text-sm text-muted-foreground">
            Subí el mismo Excel de siempre (hoja con columnas Pedido / Cantidad a comprar /
            Costo). Elegí a qué vendedor y proveedor corresponde, previsualizá y confirmá.
          </p>
          <p className="text-xs text-muted-foreground">
            Opcional: agregá una columna <span className="font-medium">document</span> con{" "}
            <span className="font-medium">remito</span> (invoice) o{" "}
            <span className="font-medium">presupuesto</span> (quote) para elegir el tipo de cada
            fila; se crea un documento por cada tipo. Si queda vacía, la fila se importa como
            remito.
          </p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
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

        <div className="space-y-1.5">
          <Label className="text-xs">Vendedor (hoja)</Label>
          <Select value={salesRepId} onValueChange={setSalesRepId}>
            <SelectTrigger>
              <SelectValue placeholder="Seleccionar" />
            </SelectTrigger>
            <SelectContent>
              {salesRepsData?.sales_reps.map((rep) => (
                <SelectItem key={rep.id} value={String(rep.id)}>
                  {rep.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label className="text-xs">Proveedor</Label>
          <Select value={supplierId} onValueChange={setSupplierId}>
            <SelectTrigger>
              <SelectValue placeholder="Seleccionar" />
            </SelectTrigger>
            <SelectContent>
              {suppliersData?.suppliers.map((supplier) => (
                <SelectItem key={supplier.id} value={String(supplier.id)}>
                  {supplier.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label className="text-xs">Fecha de la compra</Label>
          <Input
            type="date"
            value={purchaseDate}
            onChange={(e) => setPurchaseDate(e.target.value)}
          />
        </div>
      </div>

      <Button type="button" onClick={handlePreview} disabled={!canPreview || importMutation.isPending}>
        <Upload className="mr-2 h-4 w-4" />
        {importMutation.isPending ? "Analizando..." : "Previsualizar"}
      </Button>

      {preview && (
        <div className="space-y-4 rounded-xl border p-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Filas leídas</p>
              <p className="text-xl font-semibold">{preview.total_rows_read}</p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Productos a importar</p>
              <p className="text-xl font-semibold">{preview.rows_to_import.length}</p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Total</p>
              <p className="text-xl font-semibold">{formatCurrency(preview.total_amount)}</p>
            </div>
          </div>

          <p className="text-sm text-muted-foreground">
            {invoiceRowsCount} fila{invoiceRowsCount === 1 ? "" : "s"} de remito ·{" "}
            {quoteRowsCount} fila{quoteRowsCount === 1 ? "" : "s"} de presupuesto
          </p>

          {quoteRowsCount > 0 && (
            <p className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-2.5 text-xs">
              Los presupuestos de compra no afectan el stock ni la deuda con el proveedor; solo
              dejan constancia de la cotización.
            </p>
          )}

          {preview.rows_with_errors.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold">Filas con errores (se omiten)</h4>

              {/* Vista mobile: cards */}
              <div className="max-h-48 space-y-2 overflow-y-auto md:hidden">
                {preview.rows_with_errors.map((row) => (
                  <div key={row.row_number} className="rounded-lg border p-3 text-sm">
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
                    {preview.rows_with_errors.map((row) => (
                      <TableRow key={row.row_number}>
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
                {preview.rows_to_import.map((row) => (
                  <div key={row.row_number} className="rounded-lg border p-3 text-sm">
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-medium">{row.product_name}</p>
                      <DocumentTypeBadge documentType={row.document_type} />
                    </div>
                    <p className="text-muted-foreground">Cant. {row.quantity}</p>
                    <p className="text-muted-foreground">
                      Costo unit.: {formatCurrency(row.unit_cost)}
                    </p>
                  </div>
                ))}
              </div>

              {/* Vista desktop: tabla */}
              <div className="hidden max-h-64 overflow-y-auto overflow-x-auto rounded-lg border md:block">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Documento</TableHead>
                      <TableHead>Producto</TableHead>
                      <TableHead className="text-right">Cantidad</TableHead>
                      <TableHead className="text-right">Costo unit.</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {preview.rows_to_import.map((row) => (
                      <TableRow key={row.row_number}>
                        <TableCell>
                          <DocumentTypeBadge documentType={row.document_type} />
                        </TableCell>
                        <TableCell>{row.product_name}</TableCell>
                        <TableCell className="text-right">{row.quantity}</TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(row.unit_cost)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </Fragment>
          )}

          {!preview.dry_run ? (
            <p className="text-sm text-brand">
              Importación completada:{" "}
              {[
                preview.purchase_invoice_id
                  ? `remito de compra #${preview.purchase_invoice_id}`
                  : null,
                preview.purchase_quote_id
                  ? `presupuesto de compra #${preview.purchase_quote_id}`
                  : null,
              ]
                .filter(Boolean)
                .join(" y ") || "sin documentos nuevos"}
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