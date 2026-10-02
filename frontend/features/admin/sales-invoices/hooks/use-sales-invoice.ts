"use client";

import { useQuery } from "@tanstack/react-query";
import { getSalesInvoiceApi } from "@/features/admin/sales-invoices/apis/sales-invoice-api";

export function useSalesInvoice(salesInvoiceId: number | null) {
  return useQuery({
    queryKey: ["sales-invoice", salesInvoiceId],
    queryFn: () => {
      if (!salesInvoiceId) {
        throw new Error("salesInvoiceId es requerido");
      }

      return getSalesInvoiceApi(salesInvoiceId);
    },
    enabled: !!salesInvoiceId,
  });
}