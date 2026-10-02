"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { importSupplierPurchasesApi } from "@/features/admin/account-ledger/apis/account-ledger-api";

type ImportSupplierPurchasesInput = {
  file: File;
  salesRepId: number;
  supplierId: number;
  purchaseDate: string;
  sheetName?: string;
  dryRun: boolean;
};

export function useImportSupplierPurchases() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: ImportSupplierPurchasesInput) => importSupplierPurchasesApi(input),
    onSuccess: (result) => {
      if (!result.dry_run) {
        queryClient.invalidateQueries({ queryKey: ["supplier-purchases-ledger"] });
      }
    },
  });
}