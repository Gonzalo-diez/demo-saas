"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createSalesInvoiceApi } from "@/features/admin/sales-invoices/apis/sales-invoice-api";
import type { CreateSalesInvoiceInput } from "@/features/admin/sales-invoices/types";

export function useCreateSalesInvoice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateSalesInvoiceInput) => createSalesInvoiceApi(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales-invoices"] });
    },
  });
}