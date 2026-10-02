import { apiFetch } from "@/lib/fetcher";
import { z } from "zod";
import {
  analyticsCatalogEventSchema,
  analyticsDailySchema,
  analyticsClientDailyListSchema,
  analyticsClientDailySchema,
  analyticsProductDailyListSchema,
  analyticsSalesRepDailyListSchema,
  analyticsSalesRepDailySchema,
  analyticsZoneProductDailyListSchema,
  catalogEventsCountSchema,
  catalogEventsListSchema,
  categorySummaryEntrySchema,
  type AnalyticsCatalogEvent,
  type AnalyticsClientDaily,
  type AnalyticsDaily,
  type AnalyticsProductDaily,
  type AnalyticsSalesRepDaily,
  type AnalyticsZoneProductDaily,
  type CategorySummaryEntry,
} from "@/features/admin/analytics/schemas/analytics-schema";
import type {
  CatalogEventsQueryParams,
  ClientHistoryParams,
} from "@/features/admin/analytics/types";

function buildCatalogEventsQuery(params: CatalogEventsQueryParams = {}): string {
  const sp = new URLSearchParams();
  if (params.start_date) sp.set("start_date", params.start_date);
  if (params.end_date) sp.set("end_date", params.end_date);
  if (params.event_type) sp.set("event_type", params.event_type);
  if (params.product_id) sp.set("product_id", String(params.product_id));
  if (params.sales_rep_id) sp.set("sales_rep_id", String(params.sales_rep_id));
  if (params.visitor_id) sp.set("visitor_id", params.visitor_id);
  if (params.session_id) sp.set("session_id", params.session_id);
  if (params.limit !== undefined) sp.set("limit", String(params.limit));
  if (params.offset !== undefined) sp.set("offset", String(params.offset));
  const q = sp.toString();
  return q ? `/api/analytics/events?${q}` : "/api/analytics/events";
}

export async function getCatalogEventsApi(
  params: CatalogEventsQueryParams = {}
): Promise<AnalyticsCatalogEvent[]> {
  const response = await apiFetch<unknown>(buildCatalogEventsQuery(params), { method: "GET" });
  return catalogEventsListSchema.parse(response);
}

export async function getCatalogEventApi(eventId: number): Promise<AnalyticsCatalogEvent> {
  const response = await apiFetch<unknown>(`/api/analytics/events/${eventId}`, { method: "GET" });
  return analyticsCatalogEventSchema.parse(response);
}

export async function getCatalogEventsCountApi(
  params: Pick<CatalogEventsQueryParams, "start_date" | "end_date" | "event_type" | "product_id">
): Promise<number> {
  const sp = new URLSearchParams();
  if (params.start_date) sp.set("start_date", params.start_date);
  if (params.end_date) sp.set("end_date", params.end_date);
  if (params.event_type) sp.set("event_type", params.event_type);
  if (params.product_id) sp.set("product_id", String(params.product_id));
  const q = sp.toString();
  const url = q ? `/api/analytics/events/count?${q}` : "/api/analytics/events/count";
  const response = await apiFetch<unknown>(url, { method: "GET" });
  return catalogEventsCountSchema.parse(response).total;
}

export async function getCatalogEventsStatsApi(params: {
  start_date?: string;
  end_date?: string;
}): Promise<Record<string, number>> {
  const sp = new URLSearchParams();
  if (params.start_date) sp.set("start_date", params.start_date);
  if (params.end_date) sp.set("end_date", params.end_date);
  const q = sp.toString();
  const url = q ? `/api/analytics/events/stats?${q}` : "/api/analytics/events/stats";
  const response = await apiFetch<unknown>(url, { method: "GET" });
  return response as Record<string, number>;
}

export async function getAnalyticsDailyApi(targetDate: string): Promise<AnalyticsDaily> {
  const response = await apiFetch<unknown>(
    `/api/analytics/daily?target_date=${targetDate}`,
    { method: "GET" }
  );
  return analyticsDailySchema.parse(response);
}

export async function getAnalyticsDailyRangeApi(params: {
  start_date: string;
  end_date: string;
  limit?: number;
}): Promise<AnalyticsDaily[]> {
  const sp = new URLSearchParams({
    start_date: params.start_date,
    end_date: params.end_date,
  });
  if (params.limit !== undefined) sp.set("limit", String(params.limit));
  const response = await apiFetch<unknown>(
    `/api/analytics/daily/range?${sp.toString()}`,
    { method: "GET" }
  );
  return analyticsDailySchema.array().parse(response);
}

export async function getProductsDailyApi(targetDate: string): Promise<AnalyticsProductDaily[]> {
  const response = await apiFetch<unknown>(
    `/api/analytics/products/daily?target_date=${targetDate}`,
    { method: "GET" }
  );
  return analyticsProductDailyListSchema.parse(response);
}

export async function getProductDailyApi(
  productId: number,
  targetDate: string
): Promise<AnalyticsProductDaily | null> {
  const response = await apiFetch<unknown>(
    `/api/analytics/products/daily/${productId}?target_date=${targetDate}`,
    { method: "GET" }
  );
  if (!response) return null;
  return analyticsProductDailyListSchema.element.parse(response);
}

export async function getProductHistoryApi(params: {
  product_id: number;
  start_date: string;
  end_date: string;
  limit?: number;
}): Promise<AnalyticsProductDaily[]> {
  const sp = new URLSearchParams({
    start_date: params.start_date,
    end_date: params.end_date,
  });
  if (params.limit !== undefined) sp.set("limit", String(params.limit));
  const response = await apiFetch<unknown>(
    `/api/analytics/products/${params.product_id}/history?${sp.toString()}`,
    { method: "GET" }
  );
  return analyticsProductDailyListSchema.parse(response);
}

export async function getSalesRepsDailyApi(targetDate: string): Promise<AnalyticsSalesRepDaily[]> {
  const response = await apiFetch<unknown>(
    `/api/analytics/sales-reps/daily?target_date=${targetDate}`,
    { method: "GET" }
  );
  return analyticsSalesRepDailyListSchema.parse(response);
}

export async function getSalesRepDailyApi(
  salesRepId: number,
  targetDate: string
): Promise<AnalyticsSalesRepDaily | null> {
  const response = await apiFetch<unknown>(
    `/api/analytics/sales-reps/daily/${salesRepId}?target_date=${targetDate}`,
    { method: "GET" }
  );
  if (!response) return null;
  return analyticsSalesRepDailySchema.parse(response);
}

export async function getSalesRepHistoryApi(params: {
  sales_rep_id: number;
  start_date: string;
  end_date: string;
  limit?: number;
}): Promise<AnalyticsSalesRepDaily[]> {
  const sp = new URLSearchParams({
    start_date: params.start_date,
    end_date: params.end_date,
  });
  if (params.limit !== undefined) sp.set("limit", String(params.limit));
  const response = await apiFetch<unknown>(
    `/api/analytics/sales-reps/${params.sales_rep_id}/history?${sp.toString()}`,
    { method: "GET" }
  );
  return analyticsSalesRepDailyListSchema.parse(response);
}

export async function getClientsDailyApi(targetDate: string): Promise<AnalyticsClientDaily[]> {
  const response = await apiFetch<unknown>(
    `/api/analytics/clients/daily?target_date=${targetDate}`,
    { method: "GET" }
  );
  return analyticsClientDailyListSchema.parse(response);
}

export async function getClientDailyApi(
  clientId: number,
  targetDate: string
): Promise<AnalyticsClientDaily | null> {
  const response = await apiFetch<unknown>(
    `/api/analytics/clients/daily/${clientId}?target_date=${targetDate}`,
    { method: "GET" }
  );
  if (!response) return null;
  return analyticsClientDailySchema.parse(response);
}

export async function getClientHistoryApi(
  params: ClientHistoryParams
): Promise<AnalyticsClientDaily[]> {
  const sp = new URLSearchParams({
    start_date: params.start_date,
    end_date: params.end_date,
  });
  if (params.limit !== undefined) sp.set("limit", String(params.limit));
  const response = await apiFetch<unknown>(
    `/api/analytics/clients/${params.client_id}/history?${sp.toString()}`,
    { method: "GET" }
  );
  return analyticsClientDailyListSchema.parse(response);
}

export async function getZoneProductsDailyApi(
  targetDate: string
): Promise<AnalyticsZoneProductDaily[]> {
  const response = await apiFetch<unknown>(
    `/api/analytics/zones/products/daily?target_date=${targetDate}`,
    { method: "GET" }
  );
  return analyticsZoneProductDailyListSchema.parse(response);
}

export async function getZoneProductDailyApi(
  h3Index: string,
  targetDate: string
): Promise<AnalyticsZoneProductDaily | null> {
  const response = await apiFetch<unknown>(
    `/api/analytics/zones/products/daily/${h3Index}?target_date=${targetDate}`,
    { method: "GET" }
  );
  if (!response) return null;
  return analyticsZoneProductDailyListSchema.element.parse(response);
}

export type RankingProductOrderBy = "revenue" | "quantity";
export type RankingClientOrderBy = "revenue" | "orders";
export type RankingSalesRepOrderBy = "revenue" | "orders" | "products";

export async function getTopProductsApi(params: {
  start_date: string;
  end_date: string;
  order_by?: RankingProductOrderBy;
  limit?: number;
}): Promise<AnalyticsProductDaily[]> {
  const sp = new URLSearchParams({
    start_date: params.start_date,
    end_date: params.end_date,
  });
  if (params.order_by) sp.set("order_by", params.order_by);
  if (params.limit !== undefined) sp.set("limit", String(params.limit));
  const response = await apiFetch<unknown>(
    `/api/analytics/rankings/products?${sp.toString()}`,
    { method: "GET" }
  );
  return analyticsProductDailyListSchema.parse(response);
}

export async function getTopClientsApi(params: {
  start_date: string;
  end_date: string;
  order_by?: RankingClientOrderBy;
  limit?: number;
}): Promise<AnalyticsClientDaily[]> {
  const sp = new URLSearchParams({
    start_date: params.start_date,
    end_date: params.end_date,
  });
  if (params.order_by) sp.set("order_by", params.order_by);
  if (params.limit !== undefined) sp.set("limit", String(params.limit));
  const response = await apiFetch<unknown>(
    `/api/analytics/rankings/clients?${sp.toString()}`,
    { method: "GET" }
  );
  return analyticsClientDailyListSchema.parse(response);
}

export async function getTopClientCategoriesApi(params: {
  start_date: string;
  end_date: string;
  client_id?: number;
  limit?: number;
}): Promise<CategorySummaryEntry[]> {
  const sp = new URLSearchParams({
    start_date: params.start_date,
    end_date: params.end_date,
  });
  if (params.client_id !== undefined) sp.set("client_id", String(params.client_id));
  if (params.limit !== undefined) sp.set("limit", String(params.limit));
  const response = await apiFetch<unknown>(
    `/api/analytics/rankings/clients/categories?${sp.toString()}`,
    { method: "GET" }
  );
  return z.array(categorySummaryEntrySchema).parse(response);
}

export async function getTopSalesRepsApi(params: {
  start_date: string;
  end_date: string;
  order_by?: RankingSalesRepOrderBy;
  limit?: number;
}): Promise<AnalyticsSalesRepDaily[]> {
  const sp = new URLSearchParams({
    start_date: params.start_date,
    end_date: params.end_date,
  });
  if (params.order_by) sp.set("order_by", params.order_by);
  if (params.limit !== undefined) sp.set("limit", String(params.limit));
  const response = await apiFetch<unknown>(
    `/api/analytics/rankings/sales-reps?${sp.toString()}`,
    { method: "GET" }
  );
  return analyticsSalesRepDailyListSchema.parse(response);
}

export async function getAnalyticsSchedulerJobsApi(): Promise<
  {
    id: string;
    name: string;
    next_run: string | null;
  }[]
> {
  const response = await apiFetch<unknown>(
    "/api/analytics/scheduler/jobs",
    {
      method: "GET",
    }
  );

  return response as {
    id: string;
    name: string;
    next_run: string | null;
  }[];
}

export async function runAnalyticsAggregationApi(
  targetDate: string
): Promise<{ success: boolean; target_date: string }> {
  const response = await apiFetch<unknown>(
    `/api/analytics/aggregate?target_date=${targetDate}`,
    { method: "POST" }
  );
  return response as { success: boolean; target_date: string };
}