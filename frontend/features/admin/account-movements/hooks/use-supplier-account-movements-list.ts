"use client";

import { useQuery } from "@tanstack/react-query";
import { getSupplierAccountMovementsApi } from "@/features/admin/account-movements/apis/supplier-account-movements-api";
import type { SupplierAccountMovementsQueryParams } from "@/features/admin/account-movements/types";

export function useSupplierAccountMovementsList(
  params: SupplierAccountMovementsQueryParams
) {
  return useQuery({
    queryKey: ["supplier-account-movements-list", params],
    queryFn: () => getSupplierAccountMovementsApi(params),
    placeholderData: (previousData) => previousData,
  });
}
