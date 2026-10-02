"use client";

import { useState } from "react";
import { FileText, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { useImportExcelFromPdf } from "@/features/admin/products/hooks/use-import-excel-from-pdf";

type GenerateExcelFromPdfCardProps = {
  onSuccess: () => void;
};

export function GenerateExcelFromPdfCard({
  onSuccess,
}: GenerateExcelFromPdfCardProps) {
  const pdfMutation = useImportExcelFromPdf();
  const [pdfFile, setPdfFile] = useState<File | null>(null);

  async function handleGenerateFromPdf() {
    if (!pdfFile) return;
    try {
      const blob = await pdfMutation.mutateAsync(pdfFile);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "productos_importacion.xlsx";
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Excel generado y descargado", { position: "top-right" });
      setPdfFile(null);
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Error al procesar el PDF",
        { position: "top-right", duration: 4000 },
      );
    }
  }

  return (
    <div className="space-y-5 rounded-2xl border bg-background p-4 shadow-sm sm:p-6">
      <div className="flex items-start gap-3">
        <div className="rounded-xl border bg-muted/40 p-2">
          <FileText className="h-4 w-4" />
        </div>
        <div className="space-y-1">
          <h2 className="text-lg font-semibold">
            Generar Excel desde PDF de proveedor
          </h2>
          <p className="text-sm text-muted-foreground">
            Subí la lista de precios en PDF y descargá un Excel listo para
            completar y luego importar.
          </p>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_180px]">
        <div className="space-y-2">
          <label className="text-sm font-medium">Archivo PDF</label>
          <Input
            type="file"
            accept=".pdf"
            onChange={(e) => setPdfFile(e.target.files?.[0] ?? null)}
          />
        </div>
        <div className="flex items-end">
          <Button
            type="button"
            onClick={handleGenerateFromPdf}
            disabled={!pdfFile || pdfMutation.isPending}
            className="w-full"
          >
            <Upload className="mr-2 h-4 w-4" />
            {pdfMutation.isPending ? "Procesando..." : "Generar Excel"}
          </Button>
        </div>
      </div>

      {pdfMutation.error && (
        <div className="rounded-md border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {pdfMutation.error instanceof Error
            ? pdfMutation.error.message
            : "Error al procesar el PDF"}
        </div>
      )}
    </div>
  );
}
