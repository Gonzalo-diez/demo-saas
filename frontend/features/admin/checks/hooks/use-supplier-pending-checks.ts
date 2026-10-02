"use client";

import { useQuery } from "@tanstack/react-query";
import { getSupplierPendingChecksApi } from "@/features/admin/checks/apis/check-api";

export function useSupplierPendingChecks(supplierId: number | null) {
  return useQuery({
    queryKey: ["supplier-pending-checks", supplierId],
    queryFn: () => {
      if (!supplierId) {
        throw new Error("supplierId es requerido");
      }
      return getSupplierPendingChecksApi(supplierId);
    },
    enabled: !!supplierId,
  });
}
