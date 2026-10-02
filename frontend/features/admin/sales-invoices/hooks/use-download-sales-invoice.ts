"use client";

import { useMutation } from "@tanstack/react-query";
import { downloadSalesInvoicePdfApi } from "@/features/admin/sales-invoices/apis/sales-invoice-api";

type DownloadSalesInvoicePayload = {
  salesInvoiceId: number;
};

export function useDownloadSalesInvoice() {
  return useMutation({
    mutationFn: ({ salesInvoiceId }: DownloadSalesInvoicePayload) =>
      downloadSalesInvoicePdfApi(salesInvoiceId)
  });
}