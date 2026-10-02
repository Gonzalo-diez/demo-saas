"use client";

import { useQuery } from "@tanstack/react-query";
import { getPurchaseQuoteApi } from "@/features/admin/purchase-quotes/apis/purchase-quote-api";

export function usePurchaseQuote(purchaseQuoteId: number | null) {
  return useQuery({
    queryKey: ["purchase-quote", purchaseQuoteId],
    queryFn: () => {
      if (!purchaseQuoteId) {
        throw new Error("purchaseQuoteId es requerido");
      }
      return getPurchaseQuoteApi(purchaseQuoteId);
    },
    enabled: !!purchaseQuoteId,
  });
}
