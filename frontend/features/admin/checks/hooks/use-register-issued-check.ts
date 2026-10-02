"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { registerIssuedCheckApi } from "@/features/admin/checks/apis/check-api";
import type { RegisterIssuedCheckInput } from "@/features/admin/checks/types";

type RegisterIssuedCheckPayload = {
  supplierId: number;
  data: RegisterIssuedCheckInput;
};

export function useRegisterIssuedCheck() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ supplierId, data }: RegisterIssuedCheckPayload) =>
      registerIssuedCheckApi(supplierId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["checks"] });
    },
  });
}
