"use client";

import { useQuery } from "@tanstack/react-query";
import { getSalesQuoteApi } from "@/features/admin/sales-quotes/apis/sales-quote-api";

export function useSalesQuote(salesQuoteId: number | null) {
  return useQuery({
    queryKey: ["sales-quote", salesQuoteId],
    queryFn: () => {
      if (!salesQuoteId) {
        throw new Error("salesQuoteId es requerido");
      }
      return getSalesQuoteApi(salesQuoteId);
    },
    enabled: !!salesQuoteId,
  });
}
