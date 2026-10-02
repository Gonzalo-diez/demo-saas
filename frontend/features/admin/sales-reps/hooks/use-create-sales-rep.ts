"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createSalesRepApi } from "@/features/admin/sales-reps/apis/sales-reps-api";

export function useCreateSalesRep() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createSalesRepApi,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales-reps"] });
    },
  });
}