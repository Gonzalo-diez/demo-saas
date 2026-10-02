"use client";

import { useMutation } from "@tanstack/react-query";
import { previewPurchaseInvoiceImportApi } from "@/features/admin/purchase-invoices/apis/purchase-invoices-api";

export function usePurchaseInvoiceImportPreview() {
  return useMutation({
    mutationFn: (file: File) => previewPurchaseInvoiceImportApi(file),
  });
}