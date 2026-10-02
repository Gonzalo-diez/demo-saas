"use client";

import { useQuery } from "@tanstack/react-query";
import { getProductInventoryMovementsApi } from "@/features/admin/inventory-movements/apis/inventory-movements-api";

type Params = {
  productId: number | null;
  page?: number;
  pageSize?: number;
};

export function useProductInventoryMovements({
  productId,
  page = 1,
  pageSize = 20,
}: Params) {
  return useQuery({
    queryKey: ["product-inventory-movements", productId, page, pageSize],
    queryFn: () => {
      if (!productId) {
        throw new Error("productId es requerido");
      }

      return getProductInventoryMovementsApi(productId, page, pageSize);
    },
    enabled: !!productId,
    placeholderData: (previousData) => previousData,
  });
}