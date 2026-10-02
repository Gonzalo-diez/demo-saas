"use client";

import { useMutation } from "@tanstack/react-query";
import { downloadPurchaseInvoicePdfApi } from "@/features/admin/purchase-invoices/apis/purchase-invoices-api";

type DownloadPurchaseInvoicePayload = {
  purchaseInvoiceId: number;
};

export function useDownloadPurchaseInvoice() {
  return useMutation({
    mutationFn: ({ purchaseInvoiceId }: DownloadPurchaseInvoicePayload) =>
      downloadPurchaseInvoicePdfApi(purchaseInvoiceId)
  });
}