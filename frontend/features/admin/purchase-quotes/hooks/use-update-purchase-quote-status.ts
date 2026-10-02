"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updatePurchaseQuoteStatusApi } from "@/features/admin/purchase-quotes/apis/purchase-quote-api";
import type { PurchaseQuoteStatus } from "@/features/admin/purchase-quotes/types";

type UpdatePurchaseQuoteStatusPayload = {
  purchaseQuoteId: number;
  status: PurchaseQuoteStatus;
};

export function useUpdatePurchaseQuoteStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ purchaseQuoteId, status }: UpdatePurchaseQuoteStatusPayload) =>
      updatePurchaseQuoteStatusApi(purchaseQuoteId, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["purchase-quotes"] });
    },
  });
}
