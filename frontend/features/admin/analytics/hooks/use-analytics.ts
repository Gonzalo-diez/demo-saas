"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getCatalogEventsApi,
  getCatalogEventsCountApi,
  getCatalogEventsStatsApi,
  getAnalyticsDailyApi,
  getAnalyticsDailyRangeApi,
  getClientsDailyApi,
  getClientDailyApi,
  getClientHistoryApi,
  getProductsDailyApi,
  getProductDailyApi,
  getProductHistoryApi,
  getSalesRepsDailyApi,
  getSalesRepDailyApi,
  getSalesRepHistoryApi,
  getZoneProductsDailyApi,
  getTopProductsApi,
  getTopClientsApi,
  getTopClientCategoriesApi,
  getTopSalesRepsApi,
  getAnalyticsSchedulerJobsApi,
  runAnalyticsAggregationApi,
  type RankingProductOrderBy,
  type RankingClientOrderBy,
  type RankingSalesRepOrderBy,
} from "@/features/admin/analytics/apis/analytics-api";
import type {
  CatalogEventsQueryParams,
  ClientHistoryParams,
} from "@/features/admin/analytics/types";

export function useCatalogEvents(params: CatalogEventsQueryParams = {}) {
  return useQuery({
    queryKey: ["analytics", "catalog-events", params],
    queryFn: () => getCatalogEventsApi(params),
    placeholderData: (prev) => prev,
  });
}

export function useCatalogEventsCount(
  params: Pick<CatalogEventsQueryParams, "start_date" | "end_date" | "event_type" | "product_id">
) {
  return useQuery({
    queryKey: ["analytics", "catalog-events-count", params],
    queryFn: () => getCatalogEventsCountApi(params),
  });
}

export function useCatalogEventsStats(params: { start_date?: string; end_date?: string } = {}) {
  return useQuery({
    queryKey: ["analytics", "catalog-events-stats", params],
    queryFn: () => getCatalogEventsStatsApi(params),
  });
}

export function useAnalyticsDaily(targetDate: string) {
  return useQuery({
    queryKey: ["analytics", "daily", targetDate],
    queryFn: () => getAnalyticsDailyApi(targetDate),
    enabled: !!targetDate,
    retry: false,
  });
}

export function useAnalyticsDailyRange(params: {
  start_date: string;
  end_date: string;
  limit?: number;
} | null) {
  return useQuery({
    queryKey: ["analytics", "daily-range", params],
    queryFn: () => getAnalyticsDailyRangeApi(params!),
    enabled: !!params,
  });
}

export function useProductsDaily(targetDate: string) {
  return useQuery({
    queryKey: ["analytics", "products-daily", targetDate],
    queryFn: () => getProductsDailyApi(targetDate),
    enabled: !!targetDate,
  });
}

export function useProductDaily(productId: number | null, targetDate: string) {
  return useQuery({
    queryKey: ["analytics", "product-daily", productId, targetDate],
    queryFn: () => getProductDailyApi(productId!, targetDate),
    enabled: !!productId && !!targetDate,
  });
}

export function useProductHistory(params: {
  product_id: number;
  start_date: string;
  end_date: string;
  limit?: number;
} | null) {
  return useQuery({
    queryKey: ["analytics", "product-history", params],
    queryFn: () => getProductHistoryApi(params!),
    enabled: !!params,
  });
}

export function useSalesRepsDaily(targetDate: string) {
  return useQuery({
    queryKey: ["analytics", "sales-reps-daily", targetDate],
    queryFn: () => getSalesRepsDailyApi(targetDate),
    enabled: !!targetDate,
  });
}

export function useSalesRepDaily(salesRepId: number | null, targetDate: string) {
  return useQuery({
    queryKey: ["analytics", "sales-rep-daily", salesRepId, targetDate],
    queryFn: () => getSalesRepDailyApi(salesRepId!, targetDate),
    enabled: !!salesRepId && !!targetDate,
  });
}

export function useSalesRepHistory(params: {
  sales_rep_id: number;
  start_date: string;
  end_date: string;
  limit?: number;
} | null) {
  return useQuery({
    queryKey: ["analytics", "sales-rep-history", params],
    queryFn: () => getSalesRepHistoryApi(params!),
    enabled: !!params,
  });
}

export function useClientsDaily(targetDate: string) {
  return useQuery({
    queryKey: ["analytics", "clients-daily", targetDate],
    queryFn: () => getClientsDailyApi(targetDate),
    enabled: !!targetDate,
  });
}

export function useClientDaily(clientId: number | null, targetDate: string) {
  return useQuery({
    queryKey: ["analytics", "client-daily", clientId, targetDate],
    queryFn: () => getClientDailyApi(clientId!, targetDate),
    enabled: !!clientId && !!targetDate,
  });
}

export function useClientHistory(params: ClientHistoryParams | null) {
  return useQuery({
    queryKey: ["analytics", "client-history", params],
    queryFn: () => getClientHistoryApi(params!),
    enabled: !!params,
  });
}

export function useZoneProductsDaily(targetDate: string) {
  return useQuery({
    queryKey: ["analytics", "zone-products-daily", targetDate],
    queryFn: () => getZoneProductsDailyApi(targetDate),
    enabled: !!targetDate,
  });
}

export function useTopProducts(params: {
  start_date: string;
  end_date: string;
  order_by?: RankingProductOrderBy;
  limit?: number;
} | null) {
  return useQuery({
    queryKey: ["analytics", "rankings-products", params],
    queryFn: () => getTopProductsApi(params!),
    enabled: !!params,
  });
}

export function useTopClients(params: {
  start_date: string;
  end_date: string;
  order_by?: RankingClientOrderBy;
  limit?: number;
} | null) {
  return useQuery({
    queryKey: ["analytics", "rankings-clients", params],
    queryFn: () => getTopClientsApi(params!),
    enabled: !!params,
  });
}

export function useTopClientCategories(params: {
  start_date: string;
  end_date: string;
  client_id?: number;
  limit?: number;
} | null) {
  return useQuery({
    queryKey: ["analytics", "rankings-clients-categories", params],
    queryFn: () => getTopClientCategoriesApi(params!),
    enabled: !!params,
  });
}

export function useTopSalesReps(params: {
  start_date: string;
  end_date: string;
  order_by?: RankingSalesRepOrderBy;
  limit?: number;
} | null) {
  return useQuery({
    queryKey: ["analytics", "rankings-sales-reps", params],
    queryFn: () => getTopSalesRepsApi(params!),
    enabled: !!params,
  });
}

export function useAnalyticsSchedulerJobs() {
  return useQuery({
    queryKey: ["analytics", "scheduler-jobs"],
    queryFn: () => getAnalyticsSchedulerJobsApi(),
  });
}

export function useRunAggregation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (targetDate: string) => runAnalyticsAggregationApi(targetDate),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}