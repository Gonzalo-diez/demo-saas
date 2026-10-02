"use client";

import { useQuery } from "@tanstack/react-query";
import {
  getClientAgingSummaryApi,
  getClientBalanceHistoryApi,
  getClientBalanceSummaryApi,
  getClientRankingApi,
} from "@/features/admin/account-movements/apis/client-account-movements-api";
import {
  getSupplierAgingSummaryApi,
  getSupplierBalanceHistoryApi,
  getSupplierBalanceSummaryApi,
  getSupplierRankingApi,
} from "@/features/admin/account-movements/apis/supplier-account-movements-api";
import type {
  AccountMovementEntityType,
  AccountRankingOrder,
} from "@/features/admin/account-movements/types";

export function useAccountBalanceSummary(entityType: AccountMovementEntityType) {
  return useQuery({
    queryKey: ["account-movements-balance-summary", entityType],
    queryFn: () => {
      if (entityType === "client") return getClientBalanceSummaryApi();
      return getSupplierBalanceSummaryApi();
    },
  });
}

export function useAccountAgingSummary(entityType: AccountMovementEntityType) {
  return useQuery({
    queryKey: ["account-movements-aging-summary", entityType],
    queryFn: () => {
      if (entityType === "client") return getClientAgingSummaryApi();
      return getSupplierAgingSummaryApi();
    },
  });
}

export function useAccountRanking(
  entityType: AccountMovementEntityType,
  order: AccountRankingOrder,
  limit = 5
) {
  return useQuery({
    queryKey: ["account-movements-ranking", entityType, order, limit],
    queryFn: () => {
      if (entityType === "client") return getClientRankingApi(order, limit);
      return getSupplierRankingApi(order, limit);
    },
  });
}

export function useAccountBalanceHistory(
  entityType: AccountMovementEntityType,
  entityId: number | null,
  limit = 60
) {
  return useQuery({
    queryKey: ["account-movements-balance-history", entityType, entityId, limit],
    queryFn: () => {
      if (entityType === "client") return getClientBalanceHistoryApi(entityId as number, limit);
      return getSupplierBalanceHistoryApi(entityId as number, limit);
    },
    enabled: entityId !== null,
  });
}