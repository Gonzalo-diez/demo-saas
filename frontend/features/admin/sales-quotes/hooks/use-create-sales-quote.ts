"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createSalesQuoteApi } from "@/features/admin/sales-quotes/apis/sales-quote-api";
import type { CreateSalesQuoteInput } from "@/features/admin/sales-quotes/types";

export function useCreateSalesQuote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateSalesQuoteInput) => createSalesQuoteApi(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales-quotes"] });
    },
  });
}
