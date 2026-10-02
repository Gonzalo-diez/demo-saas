"use client";

import { useMutation } from "@tanstack/react-query";
import { previewSalesInvoiceImportApi } from "@/features/admin/sales-invoices/apis/sales-invoice-api";

export function useSalesInvoiceImportPreview() {
  return useMutation({
    mutationFn: (file: File) => previewSalesInvoiceImportApi(file),
  });
}