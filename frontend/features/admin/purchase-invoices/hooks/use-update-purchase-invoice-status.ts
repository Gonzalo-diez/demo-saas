"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updatePurchaseInvoiceStatusApi } from "@/features/admin/purchase-invoices/apis/purchase-invoices-api";
import type { PurchaseInvoiceStatus } from "@/features/admin/purchase-invoices/types";

type UpdatePurchaseInvoiceStatusPayload = {
  purchaseInvoiceId: number;
  status: PurchaseInvoiceStatus;
};

export function useUpdatePurchaseInvoiceStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      purchaseInvoiceId,
      status,
    }: UpdatePurchaseInvoiceStatusPayload) =>
      updatePurchaseInvoiceStatusApi(purchaseInvoiceId, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["purchase-invoices"] });
    },
  });
}