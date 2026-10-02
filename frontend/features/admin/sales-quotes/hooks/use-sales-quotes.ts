"use client";

import { useQuery } from "@tanstack/react-query";
import { getSalesQuotesApi } from "@/features/admin/sales-quotes/apis/sales-quote-api";
import type { SalesQuotesQueryParams } from "@/features/admin/sales-quotes/types";

export function useSalesQuotes(params: SalesQuotesQueryParams) {
  return useQuery({
    queryKey: ["sales-quotes", params],
    queryFn: () => getSalesQuotesApi(params),
    placeholderData: (previousData) => previousData,
  });
}
