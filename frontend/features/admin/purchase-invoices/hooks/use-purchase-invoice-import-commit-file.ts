"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { commitPurchaseInvoiceImportFileApi } from "@/features/admin/purchase-invoices/apis/purchase-invoices-api";

export function usePurchaseInvoiceImportCommitFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: commitPurchaseInvoiceImportFileApi,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["purchase-invoices"] });
    },
  });
}