"use client";

import { useQuery } from "@tanstack/react-query";
import { getProductApi } from "@/features/admin/products/apis/products-api";

export function useProduct(productId: number | null) {
  return useQuery({
    queryKey: ["product", productId],
    queryFn: () => {
      if (!productId) {
        throw new Error("productId es requerido");
      }

      return getProductApi(productId);
    },
    enabled: !!productId,
  });
}