"use client";

import { useQuery } from "@tanstack/react-query";
import { getSalesRepsApi } from "@/features/admin/sales-reps/apis/sales-reps-api";
import type { SalesRepsQueryParams } from "@/features/admin/sales-reps/types";

export function useSalesReps(params: SalesRepsQueryParams = {}) {
  return useQuery({
    queryKey: ["sales-reps", params],
    queryFn: () => getSalesRepsApi(params),
    placeholderData: (previousData) => previousData,
  });
}