"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateSalesInvoiceStatusApi } from "@/features/admin/sales-invoices/apis/sales-invoice-api";
import type { SalesInvoiceStatus } from "@/features/admin/sales-invoices/types";

type UpdateSalesInvoiceStatusPayload = {
  salesInvoiceId: number;
  status: SalesInvoiceStatus;
};

export function useUpdateSalesInvoiceStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ salesInvoiceId, status }: UpdateSalesInvoiceStatusPayload) =>
      updateSalesInvoiceStatusApi(salesInvoiceId, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales-invoices"] });
    },
  });
}