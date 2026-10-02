"use client";

import { Download, Loader2 } from "lucide-react";
import { toast } from "sonner";
import type { SalesQuote } from "@/features/admin/sales-quotes/types";
import { useDownloadSalesQuote } from "@/features/admin/sales-quotes/hooks/use-download-sales-quote";
import { Button } from "@/components/ui/button";

type DownloadSalesQuoteButtonProps = {
  salesQuote: SalesQuote;
};

export function DownloadSalesQuoteButton({ salesQuote }: DownloadSalesQuoteButtonProps) {
  const { mutateAsync, isPending } = useDownloadSalesQuote();

  async function handleDownload() {
    try {
      const blob = await mutateAsync({ salesQuoteId: salesQuote.id });

      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `presupuesto-venta-${salesQuote.quote_number}.pdf`;

      document.body.appendChild(link);
      link.click();
      link.remove();

      URL.revokeObjectURL(url);
    } catch {
      toast.error("No se pudo descargar el presupuesto.");
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
      {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
    </Button>
  );
}
