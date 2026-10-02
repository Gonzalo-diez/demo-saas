import { apiFetch, apiFetchBlob } from "@/lib/fetcher";
import type {
  CreateSalesQuoteInput,
  PaginatedSalesQuotesResponse,
  SalesQuote,
  SalesQuotesQueryParams,
  UpdateSalesQuoteStatusInput,
} from "@/features/admin/sales-quotes/types";

function buildSalesQuotesQuery(params: SalesQuotesQueryParams = {}) {
  const searchParams = new URLSearchParams();

  searchParams.set("page", String(params.page ?? 1));
  searchParams.set("page_size", String(params.page_size ?? 10));

  if (params.status && params.status !== "all") {
    searchParams.set("status", params.status);
  }

  if (params.client_id) {
    searchParams.set("client_id", String(params.client_id));
  }

  if (params.from_orders !== undefined) {
    searchParams.set("from_orders", String(params.from_orders));
  }

  return `/api/sales-quotes?${searchParams.toString()}`;
}

export async function getSalesQuotesApi(params: SalesQuotesQueryParams = {}) {
  return apiFetch<PaginatedSalesQuotesResponse>(buildSalesQuotesQuery(params), {
    method: "GET",
  });
}

export async function getSalesQuoteApi(salesQuoteId: number) {
  return apiFetch<SalesQuote>(`/api/sales-quotes/${salesQuoteId}`, {
    method: "GET",
  });
}

export async function downloadSalesQuotePdfApi(salesQuoteId: number): Promise<Blob> {
  return apiFetchBlob(`/api/sales-quotes/${salesQuoteId}/download-pdf`, {
    method: "GET",
  });
}

export async function createSalesQuoteApi(data: CreateSalesQuoteInput) {
  return apiFetch<SalesQuote>("/api/sales-quotes", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateSalesQuoteStatusApi(
  salesQuoteId: number,
  data: UpdateSalesQuoteStatusInput
) {
  return apiFetch<SalesQuote>(`/api/sales-quotes/${salesQuoteId}/status`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}
