import { apiFetch, apiFetchBlob } from "@/lib/fetcher";
import {
  SupplierImportCommitRequest,
  SupplierImportCommitResponse,
  SupplierImportPreviewResponse,
  type CreateSupplierInput,
  type Supplier,
  type SupplierListParams,
  type SupplierListResponse,
  type UpdateSupplierInput,
} from "@/features/admin/suppliers/types";

function buildSuppliersQuery(params: SupplierListParams = {}) {
  const searchParams = new URLSearchParams();

  if (params.page) {
    searchParams.set("page", String(params.page));
  }

  if (params.page_size) {
    searchParams.set("page_size", String(params.page_size));
  }

  if (params.search?.trim()) {
    searchParams.set("search", params.search.trim());
  }

  if (params.status === "active") {
    searchParams.set("is_active", "true");
  }

  if (params.status === "inactive") {
    searchParams.set("is_active", "false");
  }

  const query = searchParams.toString();
  return query ? `/api/suppliers/?${query}` : "/api/suppliers/";
}

export async function getSuppliersApi(params: SupplierListParams = {}) {
  return apiFetch<SupplierListResponse>(buildSuppliersQuery(params), {
    method: "GET",
  });
}

export async function createSupplierApi(data: CreateSupplierInput) {
  return apiFetch<Supplier>("/api/suppliers/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateSupplierApi(
  supplierId: number,
  data: UpdateSupplierInput
) {
  return apiFetch<Supplier>(`/api/suppliers/${supplierId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function toggleSupplierStatusApi(
  supplierId: number,
  nextStatus: "active" | "inactive"
) {
  const endpoint =
    nextStatus === "active"
      ? `/api/suppliers/${supplierId}/activate`
      : `/api/suppliers/${supplierId}/deactivate`;

  return apiFetch<Supplier>(endpoint, {
    method: "PATCH",
  });
}

export async function previewSuppliersImportApi(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  return apiFetch<SupplierImportPreviewResponse>("/api/suppliers/import/preview", {
    method: "POST",
    body: formData,
  });
}

export async function commitSuppliersImportApi(
  data: SupplierImportCommitRequest
) {
  return apiFetch<SupplierImportCommitResponse>("/api/suppliers/import/commit", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function commitSuppliersImportFileApi(file: File, mode: string = "upsert") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("mode", mode);

  return apiFetch<SupplierImportCommitResponse>("/api/suppliers/import/commit-file", {
    method: "POST",
    body: formData,
  });
}

export async function downloadSupplierImportSampleApi(): Promise<Blob> {
  return apiFetchBlob("/api/suppliers/import/sample-excel", {
    method: "GET",
  });
}