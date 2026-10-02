"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createPurchaseInvoiceApi } from "@/features/admin/purchase-invoices/apis/purchase-invoices-api";

export function useCreatePurchaseInvoice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createPurchaseInvoiceApi,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["purchase-invoices"] });
    },
  });
}