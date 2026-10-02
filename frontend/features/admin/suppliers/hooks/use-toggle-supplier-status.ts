"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toggleSupplierStatusApi } from "@/features/admin/suppliers/apis/suppliers-api";

type ToggleSupplierStatusPayload = {
  supplierId: number;
  nextStatus: "active" | "inactive";
  supplierName?: string;
};

export function useToggleSupplierStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ supplierId, nextStatus }: ToggleSupplierStatusPayload) =>
      toggleSupplierStatusApi(supplierId, nextStatus),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["suppliers"] });
    },
  });
}