"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  activateClientBranchApi,
  deactivateClientBranchApi,
} from "@/features/admin/clients/apis/client-branches-api";

type Payload = {
  clientId: number;
  branchId: number;
  isActive: boolean;
};

export function useToggleClientBranchStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ clientId, branchId, isActive }: Payload) =>
      isActive
        ? deactivateClientBranchApi(clientId, branchId)
        : activateClientBranchApi(clientId, branchId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["client-branches", variables.clientId],
      });
      queryClient.invalidateQueries({ queryKey: ["clients"] });
    },
  });
}