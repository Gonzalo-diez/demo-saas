"use client";

import { useQuery } from "@tanstack/react-query";
import { getPurchaseQuotesApi } from "@/features/admin/purchase-quotes/apis/purchase-quote-api";
import type { PurchaseQuotesQueryParams } from "@/features/admin/purchase-quotes/types";

export function usePurchaseQuotes(params: PurchaseQuotesQueryParams) {
  return useQuery({
    queryKey: ["purchase-quotes", params],
    queryFn: () => getPurchaseQuotesApi(params),
    placeholderData: (previousData) => previousData,
  });
}
