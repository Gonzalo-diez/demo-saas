"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { linkPurchaseInvoiceItemProductApi } from "@/features/admin/purchase-invoices/apis/purchase-invoices-api";

type LinkPurchaseInvoiceItemProductPayload = {
  purchaseInvoiceId: number;
  itemId: number;
  productId: number;
};

export function useLinkPurchaseInvoiceItemProduct() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      purchaseInvoiceId,
      itemId,
      productId,
    }: LinkPurchaseInvoiceItemProductPayload) =>
      linkPurchaseInvoiceItemProductApi(purchaseInvoiceId, itemId, productId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["purchase-invoices"] });
      queryClient.invalidateQueries({
        queryKey: ["purchase-invoice", variables.purchaseInvoiceId],
      });
    },
  });
}