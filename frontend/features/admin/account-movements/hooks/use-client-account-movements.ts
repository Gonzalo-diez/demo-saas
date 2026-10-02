"use client";

import { useQuery } from "@tanstack/react-query";
import { getClientAccountMovementsByClientApi } from "@/features/admin/account-movements/apis/client-account-movements-api";

export function useClientAccountMovements(
  clientId: number | null,
  page = 1,
  pageSize = 20
) {
  return useQuery({
    queryKey: ["client-account-movements", clientId, page, pageSize],
    queryFn: () => getClientAccountMovementsByClientApi(clientId as number, page, pageSize),
    enabled: clientId !== null,
    placeholderData: (previousData) => previousData,
  });
}