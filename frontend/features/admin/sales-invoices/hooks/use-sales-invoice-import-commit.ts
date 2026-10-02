"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { commitSalesInvoiceImportApi } from "@/features/admin/sales-invoices/apis/sales-invoice-api";
import type { SalesInvoiceImportCommitInput } from "@/features/admin/sales-invoices/types";

export function useSalesInvoiceImportCommit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SalesInvoiceImportCommitInput) =>
      commitSalesInvoiceImportApi(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales-invoices"] });
    },
  });
}