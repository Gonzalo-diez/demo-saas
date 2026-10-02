"use client";

import { useQuery } from "@tanstack/react-query";
import { getSupplierPurchasesLedgerApi } from "@/features/admin/account-ledger/apis/account-ledger-api";
import type { SupplierPurchasesLedgerQueryParams } from "@/features/admin/account-ledger/types";

export function useSupplierPurchasesLedger(
  params: SupplierPurchasesLedgerQueryParams,
  options: { enabled?: boolean } = {}
) {
  return useQuery({
    queryKey: ["supplier-purchases-ledger", params],
    queryFn: () => getSupplierPurchasesLedgerApi(params),
    placeholderData: (previousData) => previousData,
    enabled: options.enabled ?? true,
  });
}