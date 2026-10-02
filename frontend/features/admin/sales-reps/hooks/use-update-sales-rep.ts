"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateSalesRepApi } from "@/features/admin/sales-reps/apis/sales-reps-api";
import type { UpdateSalesRepInput } from "@/features/admin/sales-reps/types";

type UpdateSalesRepPayload = {
  salesRepId: number;
  data: UpdateSalesRepInput;
};

export function useUpdateSalesRep() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ salesRepId, data }: UpdateSalesRepPayload) =>
      updateSalesRepApi(salesRepId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales-reps"] });
    },
  });
}