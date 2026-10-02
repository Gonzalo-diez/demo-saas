"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createSupplierApi } from "@/features/admin/suppliers/apis/suppliers-api";

export function useCreateSupplier() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createSupplierApi,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["suppliers"] });
    },
  });
}