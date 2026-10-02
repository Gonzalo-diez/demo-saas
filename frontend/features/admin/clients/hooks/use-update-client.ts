"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateClientApi } from "@/features/admin/clients/apis/clients-api";
import type { UpdateClientInput } from "@/features/admin/clients/types";

type UpdateClientPayload = {
  clientId: number;
  data: UpdateClientInput;
};

export function useUpdateClient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ clientId, data }: UpdateClientPayload) =>
      updateClientApi(clientId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["clients"] });
      queryClient.invalidateQueries({
        queryKey: ["client", variables.clientId],
      });
    },
  });
}