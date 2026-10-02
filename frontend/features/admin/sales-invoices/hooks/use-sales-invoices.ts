"use client";

import { useQuery } from "@tanstack/react-query";
import { getSalesInvoicesApi } from "@/features/admin/sales-invoices/apis/sales-invoice-api";
import type { SalesInvoicesQueryParams } from "@/features/admin/sales-invoices/types";

export function useSalesInvoices(params: SalesInvoicesQueryParams) {
  return useQuery({
    queryKey: ["sales-invoices", params],
    queryFn: () => getSalesInvoicesApi(params),
    placeholderData: (previousData) => previousData,
  });
}