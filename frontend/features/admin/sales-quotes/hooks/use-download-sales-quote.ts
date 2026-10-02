"use client";

import { useMutation } from "@tanstack/react-query";
import { downloadSalesQuotePdfApi } from "@/features/admin/sales-quotes/apis/sales-quote-api";

type DownloadSalesQuotePayload = {
  salesQuoteId: number;
};

export function useDownloadSalesQuote() {
  return useMutation({
    mutationFn: ({ salesQuoteId }: DownloadSalesQuotePayload) =>
      downloadSalesQuotePdfApi(salesQuoteId),
  });
}
