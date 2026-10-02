"use client";

import { useMutation } from "@tanstack/react-query";
import { downloadPurchaseQuotePdfApi } from "@/features/admin/purchase-quotes/apis/purchase-quote-api";

type DownloadPurchaseQuotePayload = {
  purchaseQuoteId: number;
};

export function useDownloadPurchaseQuote() {
  return useMutation({
    mutationFn: ({ purchaseQuoteId }: DownloadPurchaseQuotePayload) =>
      downloadPurchaseQuotePdfApi(purchaseQuoteId),
  });
}
