"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateSalesQuoteStatusApi } from "@/features/admin/sales-quotes/apis/sales-quote-api";
import type { SalesQuoteStatus } from "@/features/admin/sales-quotes/types";

type UpdateSalesQuoteStatusPayload = {
  salesQuoteId: number;
  status: SalesQuoteStatus;
};

export function useUpdateSalesQuoteStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ salesQuoteId, status }: UpdateSalesQuoteStatusPayload) =>
      updateSalesQuoteStatusApi(salesQuoteId, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales-quotes"] });
    },
  });
}
