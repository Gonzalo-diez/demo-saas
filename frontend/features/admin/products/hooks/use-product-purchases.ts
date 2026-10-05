"use client";

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createProductPurchaseApi,
  getProductPurchasesApi,
} from "@/features/admin/products/apis/product-purchases-api";
import type { CreateProductPurchaseInput } from "@/features/admin/products/purchase-types";

export function useProductPurchases(productId: number, page: number, pageSize = 20) {
  return useQuery({
    queryKey: ["product-purchases", productId, page, pageSize],
    queryFn: () => getProductPurchasesApi(productId, { page, pageSize }),
    placeholderData: keepPreviousData,
  });
}

export function useCreateProductPurchase(productId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateProductPurchaseInput) =>
      createProductPurchaseApi(productId, data),
    onSuccess: () => {
      // La compra suma stock, cambia el costo promedio y (a veces) el precio del producto.
      queryClient.invalidateQueries({ queryKey: ["product-purchases", productId] });
      queryClient.invalidateQueries({ queryKey: ["product", productId] });
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["inventory-movements"] });
    },
  });
}
