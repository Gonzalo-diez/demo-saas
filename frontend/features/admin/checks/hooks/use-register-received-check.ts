"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { registerReceivedCheckApi } from "@/features/admin/checks/apis/check-api";
import type { RegisterReceivedCheckInput } from "@/features/admin/checks/types";

type RegisterReceivedCheckPayload = {
  clientId: number;
  data: RegisterReceivedCheckInput;
};

export function useRegisterReceivedCheck() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ clientId, data }: RegisterReceivedCheckPayload) =>
      registerReceivedCheckApi(clientId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["checks"] });
    },
  });
}
