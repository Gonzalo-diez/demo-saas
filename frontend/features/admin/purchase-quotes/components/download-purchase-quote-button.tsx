"use client";

import { Download, Loader2 } from "lucide-react";
import { toast } from "sonner";
import type { PurchaseQuote } from "@/features/admin/purchase-quotes/types";
import { useDownloadPurchaseQuote } from "@/features/admin/purchase-quotes/hooks/use-download-purchase-quote";
import { Button } from "@/components/ui/button";

type DownloadPurchaseQuoteButtonProps = {
  purchaseQuote: PurchaseQuote;
};

export function DownloadPurchaseQuoteButton({ purchaseQuote }: DownloadPurchaseQuoteButtonProps) {
  const { mutateAsync, isPending } = useDownloadPurchaseQuote();

  async function handleDownload() {
    try {
      const blob = await mutateAsync({ purchaseQuoteId: purchaseQuote.id });

      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `presupuesto-compra-${purchaseQuote.quote_number}.pdf`;

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
