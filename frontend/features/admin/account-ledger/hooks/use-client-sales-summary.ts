"use client";

import { useQuery } from "@tanstack/react-query";
import { getClientSalesSummaryApi } from "@/features/admin/account-ledger/apis/account-ledger-api";

export function useClientSalesSummary(params: {
  date_from?: string | null;
  date_to?: string | null;
}) {
  return useQuery({
    queryKey: ["client-sales-summary", params],
    queryFn: () => getClientSalesSummaryApi(params),
    placeholderData: (previousData) => previousData,
  });
}