import { apiFetch, apiFetchBlob } from "@/lib/fetcher";
import type {
  CreatePurchaseQuoteInput,
  PaginatedPurchaseQuotesResponse,
  PurchaseQuote,
  PurchaseQuotesQueryParams,
  UpdatePurchaseQuoteStatusInput,
} from "@/features/admin/purchase-quotes/types";

function buildPurchaseQuotesQuery(params: PurchaseQuotesQueryParams = {}) {
  const searchParams = new URLSearchParams();

  searchParams.set("page", String(params.page ?? 1));
  searchParams.set("page_size", String(params.page_size ?? 10));

  if (params.status && params.status !== "all") {
    searchParams.set("status", params.status);
  }

  if (params.supplier_id) {
    searchParams.set("supplier_id", String(params.supplier_id));
  }

  return `/api/purchase-quotes?${searchParams.toString()}`;
}

export async function getPurchaseQuotesApi(params: PurchaseQuotesQueryParams = {}) {
  return apiFetch<PaginatedPurchaseQuotesResponse>(buildPurchaseQuotesQuery(params), {
    method: "GET",
  });
}

export async function getPurchaseQuoteApi(purchaseQuoteId: number) {
  return apiFetch<PurchaseQuote>(`/api/purchase-quotes/${purchaseQuoteId}`, {
    method: "GET",
  });
}

export async function downloadPurchaseQuotePdfApi(purchaseQuoteId: number): Promise<Blob> {
  return apiFetchBlob(`/api/purchase-quotes/${purchaseQuoteId}/download-pdf`, {
    method: "GET",
  });
}

export async function createPurchaseQuoteApi(data: CreatePurchaseQuoteInput) {
  return apiFetch<PurchaseQuote>("/api/purchase-quotes", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updatePurchaseQuoteStatusApi(
  purchaseQuoteId: number,
  data: UpdatePurchaseQuoteStatusInput
) {
  return apiFetch<PurchaseQuote>(`/api/purchase-quotes/${purchaseQuoteId}/status`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}
