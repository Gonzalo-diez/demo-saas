import { apiFetch, apiFetchBlob } from "@/lib/fetcher";
import type {
  CreatePurchaseInvoiceInput,
  PurchaseInvoice,
  PurchaseInvoiceImportCommitFileInput,
  PurchaseInvoiceImportCommitInput,
  PurchaseInvoiceImportPreviewResponse,
  PurchaseInvoicesQueryParams,
  PurchaseInvoicesResponse,
  UpdatePurchaseInvoiceStatusInput,
} from "@/features/admin/purchase-invoices/types";

function buildPurchaseInvoicesQuery(params: PurchaseInvoicesQueryParams = {}) {
  const searchParams = new URLSearchParams();

  searchParams.set("page", String(params.page ?? 1));
  searchParams.set("page_size", String(params.page_size ?? 10));

  if (params.status && params.status !== "all") {
    searchParams.set("status", params.status);
  }

  return `/api/purchase-invoices?${searchParams.toString()}`;
}

export async function getPurchaseInvoicesApi(
  params: PurchaseInvoicesQueryParams = {}
) {
  return apiFetch<PurchaseInvoicesResponse>(buildPurchaseInvoicesQuery(params), {
    method: "GET",
  });
}

export async function getPurchaseInvoiceApi(purchaseInvoiceId: number) {
  return apiFetch<PurchaseInvoice>(`/api/purchase-invoices/${purchaseInvoiceId}`, {
    method: "GET",
  });
}

export async function downloadPurchaseInvoicePdfApi(purchaseInvoiceId: number): Promise<Blob> {
  return apiFetchBlob(`/api/purchase-invoices/${purchaseInvoiceId}/download-pdf`, {
    method: "GET",
  });
}

export async function createPurchaseInvoiceApi(
  data: CreatePurchaseInvoiceInput
) {
  return apiFetch<PurchaseInvoice>("/api/purchase-invoices", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updatePurchaseInvoiceStatusApi(
  purchaseInvoiceId: number,
  data: UpdatePurchaseInvoiceStatusInput
) {
  return apiFetch<PurchaseInvoice>(
    `/api/purchase-invoices/${purchaseInvoiceId}/status`,
    {
      method: "PATCH",
      body: JSON.stringify(data),
    }
  );
}

export async function linkPurchaseInvoiceItemProductApi(
  purchaseInvoiceId: number,
  itemId: number,
  productId: number
) {
  return apiFetch<PurchaseInvoice>(
    `/api/purchase-invoices/${purchaseInvoiceId}/items/${itemId}/link-product`,
    {
      method: "PATCH",
      body: JSON.stringify({ product_id: productId }),
    }
  );
}

export async function previewPurchaseInvoiceImportApi(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  return apiFetch<PurchaseInvoiceImportPreviewResponse>(
    "/api/purchase-invoices/import/preview-file",
    {
      method: "POST",
      body: formData,
    }
  );
}

export async function commitPurchaseInvoiceImportApi(
  data: PurchaseInvoiceImportCommitInput
) {
  return apiFetch<PurchaseInvoice>("/api/purchase-invoices/import/commit", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function commitPurchaseInvoiceImportFileApi(
  data: PurchaseInvoiceImportCommitFileInput
) {
  const formData = new FormData();
  formData.append("file", data.file);

  if (data.supplier_id) {
    formData.append("supplier_id", String(data.supplier_id));
  }

  if (data.notes) {
    formData.append("notes", data.notes);
  }

  return apiFetch<PurchaseInvoice>("/api/purchase-invoices/import/commit-file", {
    method: "POST",
    body: formData,
  });
}