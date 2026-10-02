"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toggleSalesRepStatusApi } from "@/features/admin/sales-reps/apis/sales-reps-api";

type ToggleSalesRepStatusPayload = {
  salesRepId: number;
  nextStatus: "active" | "inactive";
  salesRepName?: string;
};

export function useToggleSalesRepStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ salesRepId, nextStatus }: ToggleSalesRepStatusPayload) =>
      toggleSalesRepStatusApi(salesRepId, nextStatus),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sales-reps"] });
    },
  });
}