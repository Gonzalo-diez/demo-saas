"use client";

import { useQuery } from "@tanstack/react-query";
import { getClientSalesLedgerApi } from "@/features/admin/account-ledger/apis/account-ledger-api";
import type { ClientSalesLedgerQueryParams } from "@/features/admin/account-ledger/types";

export function useClientSalesLedger(
  params: ClientSalesLedgerQueryParams,
  options: { enabled?: boolean } = {}
) {
  return useQuery({
    queryKey: ["client-sales-ledger", params],
    queryFn: () => getClientSalesLedgerApi(params),
    placeholderData: (previousData) => previousData,
    enabled: options.enabled ?? true,
  });
}