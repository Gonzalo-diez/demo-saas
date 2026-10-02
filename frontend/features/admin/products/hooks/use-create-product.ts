"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createProductApi } from "@/features/admin/products/apis/products-api";

export function useCreateProduct() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createProductApi,

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["product-categories"] });
    },
  });
}