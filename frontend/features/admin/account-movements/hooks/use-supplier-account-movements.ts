"use client";

import { useQuery } from "@tanstack/react-query";
import { getSupplierAccountMovementsBySupplierApi } from "@/features/admin/account-movements/apis/supplier-account-movements-api";

export function useSupplierAccountMovements(
  supplierId: number | null,
  page = 1,
  pageSize = 20
) {
  return useQuery({
    queryKey: ["supplier-account-movements", supplierId, page, pageSize],
    queryFn: () =>
      getSupplierAccountMovementsBySupplierApi(supplierId as number, page, pageSize),
    enabled: supplierId !== null,
    placeholderData: (previousData) => previousData,
  });
}