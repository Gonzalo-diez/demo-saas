"use client";

import { useQuery } from "@tanstack/react-query";
import { getClientAccountMovementsApi } from "@/features/admin/account-movements/apis/client-account-movements-api";
import type { ClientAccountMovementsQueryParams } from "@/features/admin/account-movements/types";

export function useClientAccountMovementsList(
  params: ClientAccountMovementsQueryParams
) {
  return useQuery({
    queryKey: ["client-account-movements-list", params],
    queryFn: () => getClientAccountMovementsApi(params),
    placeholderData: (previousData) => previousData,
  });
}
