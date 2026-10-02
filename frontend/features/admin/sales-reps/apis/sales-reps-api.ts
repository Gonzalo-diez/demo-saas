import { apiFetch, apiFetchBlob } from "@/lib/fetcher";
import type {
  CreateSalesRepInput,
  SalesRep,
  SalesRepsQueryParams,
  SalesRepsResponse,
  UpdateSalesRepInput,
  SalesRepImportCommitResponse,
  SalesRepImportPreviewResponse,
  SalesRepImportCommitRequest,
} from "@/features/admin/sales-reps/types";

function buildSalesRepsQuery(params: SalesRepsQueryParams = {}) {
  const searchParams = new URLSearchParams();

  searchParams.set("page", String(params.page ?? 1));
  searchParams.set("page_size", String(params.page_size ?? 10));

  if (params.search) searchParams.set("search", params.search);
  if (params.status) searchParams.set("status", params.status);
  if (params.sort) searchParams.set("sort", params.sort);

  return `/api/sales-reps/?${searchParams.toString()}`;
}

export async function getSalesRepsApi(params: SalesRepsQueryParams = {}) {
  return apiFetch<SalesRepsResponse>(buildSalesRepsQuery(params), {
    method: "GET",
  });
}

export async function createSalesRepApi(data: CreateSalesRepInput) {
  return apiFetch<SalesRep>("/api/sales-reps/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateSalesRepApi(
  salesRepId: number,
  data: UpdateSalesRepInput
) {
  return apiFetch<SalesRep>(`/api/sales-reps/${salesRepId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function toggleSalesRepStatusApi(
  salesRepId: number,
  nextStatus: "active" | "inactive"
) {
  const endpoint =
    nextStatus === "active"
      ? `/api/sales-reps/${salesRepId}/activate`
      : `/api/sales-reps/${salesRepId}/deactivate`;

  return apiFetch<SalesRep>(endpoint, {
    method: "PATCH",
  });
}

export async function previewSalesRepImportApi(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  return apiFetch<SalesRepImportPreviewResponse>("/api/sales-reps/import/preview", {
    method: "POST",
    body: formData,
  });
}

export async function commitSalesRepImportApi(
  data: SalesRepImportCommitRequest
) {
  return apiFetch<SalesRepImportCommitResponse>("/api/sales-reps/import/commit", {
    method: "POST",
    body: JSON.stringify(data),
  })
}

export async function commitSalesRepImportFileApi(file: File, mode: string = "upsert") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("mode", mode);

  return apiFetch<SalesRepImportCommitResponse>("/api/sales-reps/import/commit-file", {
    method: "POST",
    body: formData,
  });
}

export async function downloadSalesRepImportSampleApi(): Promise<Blob> {
  return apiFetchBlob("/api/sales-rep/import/sample-excel", {
    method: "GET",
  });
}