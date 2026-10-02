"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateClientBranchApi } from "@/features/admin/clients/apis/client-branches-api";
import type { UpdateClientBranchInput } from "@/features/admin/clients/types";

type Payload = {
  clientId: number;
  branchId: number;
  data: UpdateClientBranchInput;
};

export function useUpdateClientBranch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ clientId, branchId, data }: Payload) =>
      updateClientBranchApi(clientId, branchId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["client-branches", variables.clientId],
      });
      queryClient.invalidateQueries({ queryKey: ["clients"] });
    },
  });
}