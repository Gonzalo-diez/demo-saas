"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateProductApi } from "@/features/admin/products/apis/products-api";
import type { CreateProductInput } from "@/features/admin/products/types";

type UpdateProductPayload = {
  productId: number;
  data: CreateProductInput;
};

export function useUpdateProduct() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ productId, data }: UpdateProductPayload) =>
      updateProductApi(productId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["product-categories"] });
    },
  });
}