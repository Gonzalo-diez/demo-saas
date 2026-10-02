"use client";

import { useQuery } from "@tanstack/react-query";
import { getClientPendingChecksApi } from "@/features/admin/checks/apis/check-api";

export function useClientPendingChecks(clientId: number | null) {
  return useQuery({
    queryKey: ["client-pending-checks", clientId],
    queryFn: () => {
      if (!clientId) {
        throw new Error("clientId es requerido");
      }
      return getClientPendingChecksApi(clientId);
    },
    enabled: !!clientId,
  });
}
