"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { importClientSalesApi } from "@/features/admin/account-ledger/apis/account-ledger-api";

type ImportClientSalesInput = {
  file: File;
  sheetName?: string;
  dryRun: boolean;
};

export function useImportClientSales() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: ImportClientSalesInput) => importClientSalesApi(input),
    onSuccess: (result) => {
      if (!result.dry_run) {
        queryClient.invalidateQueries({ queryKey: ["client-sales-ledger"] });
        queryClient.invalidateQueries({ queryKey: ["client-sales-summary"] });
      }
    },
  });
}