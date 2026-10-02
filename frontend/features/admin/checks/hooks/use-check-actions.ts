"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  creditCheckApi,
  depositCheckApi,
  rejectCheckApi,
} from "@/features/admin/checks/apis/check-api";
import type { RejectCheckInput } from "@/features/admin/checks/types";

export function useDepositCheck() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (checkId: number) => depositCheckApi(checkId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["checks"] });
    },
  });
}

export function useCreditCheck() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (checkId: number) => creditCheckApi(checkId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["checks"] });
      queryClient.invalidateQueries({ queryKey: ["client-account-movements"] });
      queryClient.invalidateQueries({ queryKey: ["supplier-account-movements"] });
      // Al acreditar se mueve el saldo: refrescar también los ledgers por documento.
      queryClient.invalidateQueries({ queryKey: ["client-sales-ledger"] });
      queryClient.invalidateQueries({ queryKey: ["client-sales-summary"] });
      queryClient.invalidateQueries({ queryKey: ["supplier-purchases-ledger"] });
    },
  });
}

type RejectCheckPayload = {
  checkId: number;
  data: RejectCheckInput;
};

export function useRejectCheck() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ checkId, data }: RejectCheckPayload) => rejectCheckApi(checkId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["checks"] });
    },
  });
}
