"use client";

import { useQuery } from "@tanstack/react-query";
import { getPurchaseInvoicesApi } from "@/features/admin/purchase-invoices/apis/purchase-invoices-api";
import type {
  PurchaseInvoiceStatus,
  PurchaseInvoicesQueryParams,
} from "@/features/admin/purchase-invoices/types";

type UsePurchaseInvoicesParams = {
  page: number;
  page_size: number;
  status: PurchaseInvoiceStatus | "all";
};

export function usePurchaseInvoices(params: UsePurchaseInvoicesParams) {
  return useQuery({
    queryKey: ["purchase-invoices", params],
    queryFn: () => getPurchaseInvoicesApi(params as PurchaseInvoicesQueryParams),
    placeholderData: (previousData) => previousData,
  });
}