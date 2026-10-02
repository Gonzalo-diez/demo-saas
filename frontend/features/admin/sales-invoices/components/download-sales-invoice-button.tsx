"use client";

import { Download, Loader2 } from "lucide-react";
import { toast } from "sonner";
import type { SalesInvoice } from "@/features/admin/sales-invoices/types";
import { useDownloadSalesInvoice } from "@/features/admin/sales-invoices/hooks/use-download-sales-invoice";
import { Button } from "@/components/ui/button";

type DownloadSalesInvoiceButtonProps = {
  salesInvoice: SalesInvoice;
};

export function DownloadSalesInvoiceButton({
  salesInvoice,
}: DownloadSalesInvoiceButtonProps) {
  const { mutateAsync, isPending } = useDownloadSalesInvoice();

  async function handleDownload() {
    try {
      const blob = await mutateAsync({
        salesInvoiceId: salesInvoice.id,
      });

      const url = URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = `remito-venta-${salesInvoice.invoice_number}.pdf`;

      document.body.appendChild(link);
      link.click();
      link.remove();

      URL.revokeObjectURL(url);
    } catch {
      toast.error("No se pudo descargar el remito.");
    }
  }

  return (
    <Button
      variant="outline"
      size="icon"
      onClick={handleDownload}
      disabled={isPending}
      title="Descargar PDF"
    >
      {isPending ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <Download className="h-4 w-4" />
      )}
    </Button>
  );
}