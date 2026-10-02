"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { commitSalesInvoiceImportFileApi } from "@/features/admin/sales-invoices/apis/sales-invoice-api";
import type { SalesInvoiceImportCommitFileInput } from "@/features/admin/sales-invoices/types";

export function useSalesInvoiceImportCommitFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SalesInvoiceImportCommitFileInput) =>
      commitSalesInvoiceImportFileApi(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales-invoices"] });
    },
  });
}