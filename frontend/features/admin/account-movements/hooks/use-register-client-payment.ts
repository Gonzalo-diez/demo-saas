"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { registerClientPaymentApi } from "@/features/admin/account-movements/apis/client-account-movements-api";
import type { RegisterClientPaymentInput } from "@/features/admin/account-movements/types";

type RegisterClientPaymentPayload = {
  clientId: number;
  data: RegisterClientPaymentInput;
};

export function useRegisterClientPayment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ clientId, data }: RegisterClientPaymentPayload) =>
      registerClientPaymentApi(clientId, data),

    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["client-account-movements", variables.clientId],
      });
      queryClient.invalidateQueries({ queryKey: ["clients"] });
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