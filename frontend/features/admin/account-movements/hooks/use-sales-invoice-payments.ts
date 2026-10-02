"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  getSalesInvoicePaymentsApi,
  registerSalesInvoicePaymentApi,
} from "@/features/admin/account-movements/apis/sales-invoice-payments-api";
import type { RegisterSalesInvoicePaymentInput } from "@/features/admin/account-movements/types";

export function useSalesInvoicePayments(salesInvoiceId: number | null) {
  return useQuery({
    queryKey: ["sales-invoice-payments", salesInvoiceId],
    queryFn: () => getSalesInvoicePaymentsApi(salesInvoiceId as number),
    enabled: salesInvoiceId !== null,
  });
}

type RegisterSalesInvoicePaymentPayload = {
  salesInvoiceId: number;
  data: RegisterSalesInvoicePaymentInput;
};

export function useRegisterSalesInvoicePayment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ salesInvoiceId, data }: RegisterSalesInvoicePaymentPayload) =>
      registerSalesInvoicePaymentApi(salesInvoiceId, data),

    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["sales-invoice-payments", variables.salesInvoiceId],
      });
      queryClient.invalidateQueries({ queryKey: ["sales-invoices"] });

      toast.success("Cobro registrado");
    },

    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "No se pudo registrar el cobro"
      );
    },
  });
}