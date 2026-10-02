"use client";

import { useQuery } from "@tanstack/react-query";
import { getClientBranchesApi } from "@/features/admin/clients/apis/client-branches-api";

export function useClientBranches(clientId: number | null) {
  return useQuery({
    queryKey: ["client-branches", clientId],
    queryFn: () => getClientBranchesApi(clientId as number),
    enabled: !!clientId,
  });
}