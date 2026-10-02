import { apiFetch, apiFetchBlob } from "@/lib/fetcher";
import type {
  CreateSalesInvoiceInput,
  PaginatedSalesInvoicesResponse,
  SalesInvoice,
  SalesInvoiceImportCommitFileInput,
  SalesInvoiceImportCommitInput,
  SalesInvoiceImportPreviewResponse,
  SalesInvoicesQueryParams,
  UpdateSalesInvoiceStatusInput,
} from "@/features/admin/sales-invoices/types";

function buildSalesInvoicesQuery(params: SalesInvoicesQueryParams = {}) {
  const searchParams = new URLSearchParams();

  searchParams.set("page", String(params.page ?? 1));
  searchParams.set("page_size", String(params.page_size ?? 10));

  if (params.status && params.status !== "all") {
    searchParams.set("status", params.status);
  }

  return `/api/sales-invoices?${searchParams.toString()}`;
}

export async function getSalesInvoicesApi(
  params: SalesInvoicesQueryParams = {}
) {
  return apiFetch<PaginatedSalesInvoicesResponse>(
    buildSalesInvoicesQuery(params),
    {
      method: "GET",
    }
  );
}

export async function getSalesInvoiceApi(salesInvoiceId: number) {
  return apiFetch<SalesInvoice>(`/api/sales-invoices/${salesInvoiceId}`, {
    method: "GET",
  });
}

export async function downloadSalesInvoicePdfApi(salesInvoiceId: number): Promise<Blob> {
  return apiFetchBlob(`/api/sales-invoices/${salesInvoiceId}/download-pdf`, {
    method: "GET",
  });
}

export async function createSalesInvoiceApi(data: CreateSalesInvoiceInput) {
  return apiFetch<SalesInvoice>("/api/sales-invoices", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateSalesInvoiceStatusApi(
  salesInvoiceId: number,
  data: UpdateSalesInvoiceStatusInput
) {
  return apiFetch<SalesInvoice>(`/api/sales-invoices/${salesInvoiceId}/status`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function previewSalesInvoiceImportApi(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  return apiFetch<SalesInvoiceImportPreviewResponse>(
    "/api/sales-invoices/import/preview-file",
    {
      method: "POST",
      body: formData,
    }
  );
}

export async function commitSalesInvoiceImportApi(
  data: SalesInvoiceImportCommitInput
) {
  return apiFetch<SalesInvoice>("/api/sales-invoices/import/commit", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function commitSalesInvoiceImportFileApi(
  data: SalesInvoiceImportCommitFileInput
) {
  const formData = new FormData();
  formData.append("file", data.file);

  if (data.client_id) {
    formData.append("client_id", String(data.client_id));
  }

  if (data.client_branch_id) {
    formData.append("client_branch_id", String(data.client_branch_id));
  }

  if (data.notes) {
    formData.append("notes", data.notes);
  }

  return apiFetch<SalesInvoice>("/api/sales-invoices/import/commit-file", {
    method: "POST",
    body: formData,
  });
}