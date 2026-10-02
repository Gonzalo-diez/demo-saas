"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toggleProductStatusApi } from "@/features/admin/products/apis/products-api";

type ToggleProductStatusPayload = {
  productId: number;
  nextStatus: "active" | "inactive";
  productName?: string;
};

export function useToggleProductStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ productId, nextStatus }: ToggleProductStatusPayload) =>
      toggleProductStatusApi(productId, nextStatus),

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
    },
  });
}