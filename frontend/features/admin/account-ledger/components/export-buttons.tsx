"use client";

import { useState } from "react";
import { toast } from "sonner";
import { FileDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { triggerBlobDownload } from "@/lib/fetcher";
import {
  exportLedgerApi,
  type LedgerExportTab,
} from "@/features/admin/account-ledger/apis/account-ledger-api";

type ExportButtonsProps = {
  tab: LedgerExportTab;
  params: {
    sales_rep_id?: number | null;
    client_id?: number | null;
    date_from?: string | null;
    date_to?: string | null;
  };
};

export function ExportButtons({ tab, params }: ExportButtonsProps) {
  const [loadingFormat, setLoadingFormat] = useState<"xlsx" | "pdf" | null>(null);

  async function handleExport(format: "xlsx" | "pdf") {
    setLoadingFormat(format);
    try {
      const { blob, filename } = await exportLedgerApi(tab, format, params);
      triggerBlobDownload(blob, filename);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "No se pudo exportar");
    } finally {
      setLoadingFormat(null);
    }
  }

  return (
    <div className="flex items-center gap-2">
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => handleExport("xlsx")}
        disabled={loadingFormat !== null}
      >
        <FileDown className="mr-1.5 h-3.5 w-3.5" />
        {loadingFormat === "xlsx" ? "Generando..." : "Excel"}
      </Button>
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => handleExport("pdf")}
        disabled={loadingFormat !== null}
      >
        <FileDown className="mr-1.5 h-3.5 w-3.5" />
        {loadingFormat === "pdf" ? "Generando..." : "PDF"}
      </Button>
    </div>
  );
}