"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { commitPurchaseInvoiceImportApi } from "@/features/admin/purchase-invoices/apis/purchase-invoices-api";
import type { PurchaseInvoiceImportCommitInput } from "@/features/admin/purchase-invoices/types";

export function usePurchaseInvoiceImportCommit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: PurchaseInvoiceImportCommitInput) =>
      commitPurchaseInvoiceImportApi(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["purchase-invoices"] });
    },
  });
}