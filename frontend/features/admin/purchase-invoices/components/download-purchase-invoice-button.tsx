"use client";

import { Download, Loader2 } from "lucide-react";
import { toast } from "sonner";
import type { PurchaseInvoice } from "@/features/admin/purchase-invoices/types";
import { useDownloadPurchaseInvoice } from "@/features/admin/purchase-invoices/hooks/use-download-purchase-invoice";
import { Button } from "@/components/ui/button";

type DownloadPurchaseInvoiceButtonProps = {
  purchaseInvoice: PurchaseInvoice;
};

export function DownloadPurchaseInvoiceButton({
  purchaseInvoice,
}: DownloadPurchaseInvoiceButtonProps) {
  const { mutateAsync, isPending } = useDownloadPurchaseInvoice();

  async function handleDownload() {
    try {
      const blob = await mutateAsync({
        purchaseInvoiceId: purchaseInvoice.id,
      });

      const url = URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = `remito-compra-${purchaseInvoice.invoice_number}.pdf`;

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