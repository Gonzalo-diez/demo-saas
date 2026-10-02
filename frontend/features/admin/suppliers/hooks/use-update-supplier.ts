"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateSupplierApi } from "@/features/admin/suppliers/apis/suppliers-api";
import type { UpdateSupplierInput } from "@/features/admin/suppliers/types";

type UpdateSupplierPayload = {
  supplierId: number;
  data: UpdateSupplierInput;
};

export function useUpdateSupplier() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ supplierId, data }: UpdateSupplierPayload) =>
      updateSupplierApi(supplierId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["suppliers"] });
    },
  });
}