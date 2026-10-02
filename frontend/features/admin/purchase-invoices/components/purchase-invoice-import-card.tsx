"use client";

import { Fragment, useMemo, useState } from "react";
import { toast } from "sonner";
import { FileText, Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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

import { useSuppliers } from "@/features/admin/suppliers/hooks/use-suppliers";
import { usePurchaseInvoiceImportPreview } from "@/features/admin/purchase-invoices/hooks/use-purchase-invoice-import-preview";
import { usePurchaseInvoiceImportCommitFile } from "@/features/admin/purchase-invoices/hooks/use-purchase-invoice-import-commit-file";
import type { PurchaseInvoiceImportPreviewResponse } from "@/features/admin/purchase-invoices/types";

function formatMoney(value: string | null) {
  const numericValue = Number(value ?? 0);

  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 2,
  }).format(Number.isNaN(numericValue) ? 0 : numericValue);
}

type ImportPurchaseInvoiceCardProps = {
  onSuccess: () => void;
};

export function PurchaseInvoiceImportCard({ onSuccess }: ImportPurchaseInvoiceCardProps) {
  const suppliersQuery = useSuppliers({
    page: 1,
    page_size: 20,
    search: "",
    status: "active",
  });

  const previewMutation = usePurchaseInvoiceImportPreview();
  const commitFileMutation = usePurchaseInvoiceImportCommitFile();

  const [file, setFile] = useState<File | null>(null);
  const [supplierId, setSupplierId] = useState<number | null>(null);
  const [notes, setNotes] = useState("");
  const [previewData, setPreviewData] =
    useState<PurchaseInvoiceImportPreviewResponse | null>(null);

  const suppliers = suppliersQuery.data?.suppliers ?? [];
  const itemPreview = useMemo(() => previewData?.items.slice(0, 10) ?? [], [previewData]);

  async function handlePreview() {
    try {
      if (!file) return;
      const result = await previewMutation.mutateAsync(file);
      setPreviewData(result);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "No se pudo analizar el archivo", {
        position: "top-right",
        duration: 4000,
      });
    }
  }

  async function handleCommitFile() {
    try {
      if (!file) return;

      await commitFileMutation.mutateAsync({
        file,
        supplier_id: supplierId,
        notes: notes || null,
      });

      toast.success("Remito importado correctamente", {
        position: "top-right",
        duration: 4000,
      });

      setFile(null);
      setSupplierId(null);
      setNotes("");
      setPreviewData(null);
      onSuccess();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "No se pudo importar la remito", {
        position: "top-right",
        duration: 4000,
      });
    }
  }

  return (
    <div className="space-y-5 rounded-2xl border bg-background p-4 shadow-sm sm:p-6">
      <div className="flex items-start gap-3">
        <div className="rounded-xl border bg-muted/40 p-2">
          <FileText className="h-4 w-4" />
        </div>

        <div className="space-y-1">
          <h2 className="text-base font-semibold sm:text-lg">Importar remito por archivo</h2>
          <p className="text-sm text-muted-foreground">
            Subí un remito, revisá el preview y después confirmá la importación.
          </p>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_260px]">
        <div className="space-y-2">
          <label className="text-sm font-medium">Archivo</label>
          <Input
            type="file"
            accept=".pdf"
            onChange={(e) => {
              const selectedFile = e.target.files?.[0] ?? null;
              setFile(selectedFile);
              setPreviewData(null);
            }}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Proveedor opcional para vincular</label>
          <Select
            value={supplierId ? String(supplierId) : "__empty__"}
            onValueChange={(value) => setSupplierId(value === "__empty__" ? null : Number(value))}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Seleccionar proveedor" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__empty__">Sin seleccionar</SelectItem>
              {suppliers.map((supplier) => (
                <SelectItem key={supplier.id} value={String(supplier.id)}>
                  {supplier.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium">Notas</label>
        <Input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Opcional" />
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <Button
          type="button"
          variant="outline"
          className="w-full sm:w-auto"
          onClick={handlePreview}
          disabled={!file || previewMutation.isPending}
        >
          <Upload className="mr-2 h-4 w-4" />
          {previewMutation.isPending ? "Analizando..." : "Previsualizar"}
        </Button>

        <Button
          type="button"
          className="w-full sm:w-auto"
          onClick={handleCommitFile}
          disabled={!file || commitFileMutation.isPending}
        >
          {commitFileMutation.isPending ? "Importando..." : "Importar archivo"}
        </Button>
      </div>

      {previewData && (
        <div className="space-y-4 rounded-xl border p-4">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Proveedor</p>
              <p className="break-words font-medium">{previewData.supplier_name ?? "-"}</p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Número</p>
              <p className="break-words font-medium">{previewData.invoice_number ?? "-"}</p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Fecha</p>
              <p className="font-medium">{previewData.invoice_date ?? "-"}</p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Total detectado</p>
              <p className="font-medium">{formatMoney(previewData.total_amount)}</p>
            </div>
          </div>

          {previewData.warnings.length > 0 && (
            <div className="rounded-lg border border-kraft/20 bg-kraft/10 p-3 text-sm text-kraft">
              <p className="mb-2 font-medium">Advertencias</p>
              <div className="space-y-1">
                {previewData.warnings.map((warning, index) => (
                  <p key={index}>{warning}</p>
                ))}
              </div>
            </div>
          )}

          {previewData.errors.length > 0 && (
            <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
              <p className="mb-2 font-medium">Errores detectados</p>
              <div className="space-y-1">
                {previewData.errors.map((error, index) => (
                  <p key={index}>{error}</p>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-3">
            <h3 className="text-sm font-semibold">Ítems detectados</h3>

            {itemPreview.length === 0 ? (
              <div className="rounded-xl border px-4 py-8 text-center text-sm text-muted-foreground">
                No se detectaron ítems.
              </div>
            ) : (
              <Fragment>
                <div className="space-y-3 md:hidden">
                  {itemPreview.map((item, index) => (
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
                          <TableHead>Subtotal</TableHead>
                          <TableHead>Confianza</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {itemPreview.map((item, index) => (
                          <TableRow key={index}>
                            <TableCell>{item.product_name ?? "-"}</TableCell>
                            <TableCell>{item.quantity ?? "-"}</TableCell>
                            <TableCell>{formatMoney(item.unit_cost)}</TableCell>
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
      )}
    </div>
  );
}