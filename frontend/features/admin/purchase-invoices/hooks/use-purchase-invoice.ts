"use client";

import { useQuery } from "@tanstack/react-query";
import { getPurchaseInvoiceApi } from "@/features/admin/purchase-invoices/apis/purchase-invoices-api";

export function usePurchaseInvoice(purchaseInvoiceId: number | null) {
  return useQuery({
    queryKey: ["purchase-invoice", purchaseInvoiceId],
    queryFn: () => {
      if (!purchaseInvoiceId) {
        throw new Error("purchaseInvoiceId es requerido");
      }

      return getPurchaseInvoiceApi(purchaseInvoiceId);
    },
    enabled: !!purchaseInvoiceId,
  });
}