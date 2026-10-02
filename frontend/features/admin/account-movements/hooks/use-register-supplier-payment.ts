"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { registerSupplierPaymentApi } from "@/features/admin/account-movements/apis/supplier-account-movements-api";
import type { RegisterSupplierPaymentInput } from "@/features/admin/account-movements/types";

type RegisterSupplierPaymentPayload = {
  supplierId: number;
  data: RegisterSupplierPaymentInput;
};

export function useRegisterSupplierPayment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ supplierId, data }: RegisterSupplierPaymentPayload) =>
      registerSupplierPaymentApi(supplierId, data),

    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["supplier-account-movements", variables.supplierId],
      });
      queryClient.invalidateQueries({ queryKey: ["suppliers"] });
      queryClient.invalidateQueries({ queryKey: ["purchase-invoices"] });

      toast.success("Pago registrado");
    },

    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "No se pudo registrar el pago"
      );
    },
  });
}