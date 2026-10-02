"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createPurchaseQuoteApi } from "@/features/admin/purchase-quotes/apis/purchase-quote-api";
import type { CreatePurchaseQuoteInput } from "@/features/admin/purchase-quotes/types";

export function useCreatePurchaseQuote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreatePurchaseQuoteInput) => createPurchaseQuoteApi(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["purchase-quotes"] });
    },
  });
}
