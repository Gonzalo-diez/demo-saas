"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createClientBranchApi } from "@/features/admin/clients/apis/client-branches-api";
import type { CreateClientBranchInput } from "@/features/admin/clients/types";

type Payload = {
  clientId: number;
  data: CreateClientBranchInput;
};

export function useCreateClientBranch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ clientId, data }: Payload) =>
      createClientBranchApi(clientId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["client-branches", variables.clientId],
      });
      queryClient.invalidateQueries({ queryKey: ["clients"] });
      queryClient.invalidateQueries({ queryKey: ["clients-map"] });
    },
  });
}