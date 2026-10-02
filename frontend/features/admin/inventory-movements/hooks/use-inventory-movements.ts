"use client";

import { useQuery } from "@tanstack/react-query";
import { getInventoryMovementsApi } from "@/features/admin/inventory-movements/apis/inventory-movements-api";
import type { InventoryMovementsQueryParams } from "@/features/admin/inventory-movements/types";

export function useInventoryMovements(params: InventoryMovementsQueryParams) {
  return useQuery({
    queryKey: ["inventory-movements", params],
    queryFn: () => getInventoryMovementsApi(params),
    placeholderData: (previousData) => previousData,
  });
}