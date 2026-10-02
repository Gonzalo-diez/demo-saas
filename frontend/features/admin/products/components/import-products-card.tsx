"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Download, FileSpreadsheet, Upload } from "lucide-react";

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

import { useProductsImportPreview } from "@/features/admin/products/hooks/use-products-import-preview";
import { useProductsImportCommit } from "@/features/admin/products/hooks/use-products-import-commit";
import { useDownloadProductImportSample } from "@/features/admin/products/hooks/use-download-product-import-sample";
import { triggerBlobDownload } from "@/lib/fetcher";
import type {
  ImportMode,
  ProductImportPreviewResponse,
  ProductImportRow,
} from "@/features/admin/products/types";

type ImportProductsCardProps = {
  onSuccess: () => void;
};

export function ImportProductsCard({ onSuccess }: ImportProductsCardProps) {
  const previewMutation = useProductsImportPreview();
  const commitMutation = useProductsImportCommit();
  const downloadSampleMutation = useDownloadProductImportSample();

  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<ImportMode>("upsert");
  const [previewData, setPreviewData] =
    useState<ProductImportPreviewResponse | null>(null);

  const hasValidRows = (previewData?.rows_valid.length ?? 0) > 0;
  const hasInvalidRows = (previewData?.rows_invalid.length ?? 0) > 0;

  const invalidPreview = useMemo(() => {
    return previewData?.rows_invalid.slice(0, 10) ?? [];
  }, [previewData]);

  async function handleDownloadSample() {
    try {
      const blob = await downloadSampleMutation.mutateAsync();
      triggerBlobDownload(blob, "productos_ejemplo.xlsx");
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "No se pudo descargar el Excel de ejemplo",
        { position: "top-right", duration: 4000 },
      );
    }
  }

  async function handlePreview() {
    try {
      if (!file) return;

      const result = await previewMutation.mutateAsync(file);
      setPreviewData(result);
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "No se pudo analizar el archivo",
        {
          position: "top-right",
          duration: 4000,
        },
      );
    }
  }

  async function handleCommit() {
    try {
      if (!previewData || previewData.rows_valid.length === 0) return;

      await commitMutation.mutateAsync({
        rows: previewData.rows_valid as ProductImportRow[],
        mode,
      });

      toast.success("Importación completada", {
        position: "top-right",
        duration: 4000,
      });

      setFile(null);
      setPreviewData(null);
      onSuccess();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Error al importar productos",
        {
          position: "top-right",
          duration: 4000,
        },
      );
    }
  }

  return (
    <div className="space-y-5 rounded-2xl border bg-background p-4 shadow-sm sm:p-6">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="rounded-xl border bg-muted/40 p-2">
            <FileSpreadsheet className="h-4 w-4" />
          </div>

          <div className="space-y-1">
            <h2 className="text-lg font-semibold">
              Importar productos por Excel
            </h2>
            <p className="text-sm text-muted-foreground">
              Subí un archivo, revisá las filas válidas e inválidas, y después
              confirmá.
            </p>
            <p className="text-xs text-muted-foreground">
              El archivo debe incluir columnas como SKU, nombre, costo unitario,
              precio de venta y stock.
            </p>
          </div>
        </div>

        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleDownloadSample}
          disabled={downloadSampleMutation.isPending}
          className="shrink-0"
        >
          <Download className="mr-2 h-4 w-4" />
          {downloadSampleMutation.isPending
            ? "Descargando..."
            : "Descargar ejemplo"}
        </Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_220px_180px]">
        <div className="space-y-2">
          <label className="text-sm font-medium">Archivo Excel</label>
          <Input
            type="file"
            accept=".xlsx,.xls"
            onChange={(e) => {
              const selectedFile = e.target.files?.[0] ?? null;
              setFile(selectedFile);
              setPreviewData(null);
            }}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Modo</label>
          <Select
            value={mode}
            onValueChange={(value) => setMode(value as ImportMode)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Seleccionar modo" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="upsert">Upsert</SelectItem>
              <SelectItem value="create">Solo crear</SelectItem>
              <SelectItem value="update">Solo actualizar</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-end">
          <Button
            type="button"
            onClick={handlePreview}
            disabled={!file || previewMutation.isPending}
            className="w-full"
          >
            <Upload className="mr-2 h-4 w-4" />
            {previewMutation.isPending ? "Analizando..." : "Previsualizar"}
          </Button>
        </div>
      </div>

      {previewMutation.error && (
        <div className="rounded-md border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {previewMutation.error instanceof Error
            ? previewMutation.error.message
            : "No se pudo analizar el archivo"}
        </div>
      )}

      {previewData && (
        <div className="space-y-4 rounded-xl border p-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Total filas</p>
              <p className="text-xl font-semibold">{previewData.total_rows}</p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Válidas</p>
              <p className="text-xl font-semibold">{previewData.valid_rows}</p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Inválidas</p>
              <p className="text-xl font-semibold">
                {previewData.invalid_rows}
              </p>
            </div>
          </div>

          {hasInvalidRows && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold">Errores detectados</h3>

              <div className="grid gap-3 sm:hidden">
                {invalidPreview.map((row) => (
                  <div key={row.row_number} className="rounded-xl border p-3">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-semibold">
                        Fila {row.row_number}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        SKU: {String(row.data?.sku ?? "-")}
                      </p>
                    </div>

                    <div className="mt-3 grid gap-2 text-sm">
                      <div>
                        <p className="text-xs text-muted-foreground">Nombre</p>
                        <p>{String(row.data?.name ?? "-")}</p>
                      </div>
                      <div className="grid gap-2 xs:grid-cols-2 sm:grid-cols-2">
                        <div>
                          <p className="text-xs text-muted-foreground">Costo</p>
                          <p>{String(row.data?.unit_cost ?? "-")}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">
                            Precio
                          </p>
                          <p>{String(row.data?.unit_price ?? "-")}</p>
                        </div>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Errores</p>
                        <div className="mt-1 space-y-1">
                          {row.errors.map((error, index) => (
                            <p key={index} className="text-sm text-destructive">
                              {error}
                            </p>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="hidden overflow-hidden rounded-xl border sm:block">
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Fila</TableHead>
                        <TableHead>SKU</TableHead>
                        <TableHead>Nombre</TableHead>
                        <TableHead>Costo</TableHead>
                        <TableHead>Precio</TableHead>
                        <TableHead>Errores</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {invalidPreview.map((row) => (
                        <TableRow key={row.row_number}>
                          <TableCell>{row.row_number}</TableCell>
                          <TableCell>{String(row.data?.sku ?? "-")}</TableCell>
                          <TableCell>{String(row.data?.name ?? "-")}</TableCell>
                          <TableCell>
                            {String(row.data?.unit_cost ?? "-")}
                          </TableCell>
                          <TableCell>
                            {String(row.data?.unit_price ?? "-")}
                          </TableCell>
                          <TableCell>
                            <div className="space-y-1">
                              {row.errors.map((error, index) => (
                                <p key={index} className="text-destructive">
                                  {error}
                                </p>
                              ))}
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>

              {previewData.rows_invalid.length > 10 && (
                <p className="text-xs text-muted-foreground">
                  Mostrando solo los primeros 10 errores.
                </p>
              )}
            </div>
          )}

          <div className="flex flex-col gap-2 border-t pt-4 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-muted-foreground">
              {hasValidRows
                ? `${previewData.valid_rows} filas listas para importar.`
                : "No hay filas válidas para importar."}
            </p>

            <Button
              type="button"
              onClick={handleCommit}
              disabled={!hasValidRows || commitMutation.isPending}
              className="w-full sm:w-auto"
            >
              {commitMutation.isPending
                ? "Importando..."
                : "Confirmar importación"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}