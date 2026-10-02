import { apiFetch } from "@/lib/fetcher";
import type {
  Check,
  CheckPendingSummaryResponse,
  ChecksQueryParams,
  DocumentPendingChecksResponse,
  PaginatedChecksResponse,
  RegisterIssuedCheckInput,
  RegisterReceivedCheckInput,
  RejectCheckInput,
} from "@/features/admin/checks/types";

function buildChecksQuery(params: ChecksQueryParams = {}) {
  const searchParams = new URLSearchParams();

  searchParams.set("page", String(params.page ?? 1));
  searchParams.set("page_size", String(params.page_size ?? 20));

  if (params.direction && params.direction !== "all") {
    searchParams.set("direction", params.direction);
  }

  if (params.status && params.status !== "all") {
    searchParams.set("status", params.status);
  }

  if (params.client_id) {
    searchParams.set("client_id", String(params.client_id));
  }

  if (params.supplier_id) {
    searchParams.set("supplier_id", String(params.supplier_id));
  }

  if (params.due_before) {
    searchParams.set("due_before", params.due_before);
  }

  return `/api/checks?${searchParams.toString()}`;
}

export async function getChecksApi(params: ChecksQueryParams = {}) {
  return apiFetch<PaginatedChecksResponse>(buildChecksQuery(params), { method: "GET" });
}

export async function getCheckApi(checkId: number) {
  return apiFetch<Check>(`/api/checks/${checkId}`, { method: "GET" });
}

export async function getClientPendingChecksApi(clientId: number) {
  return apiFetch<CheckPendingSummaryResponse>(
    `/api/checks/by-client/${clientId}/pending-summary`,
    { method: "GET" }
  );
}

export async function getSupplierPendingChecksApi(supplierId: number) {
  return apiFetch<CheckPendingSummaryResponse>(
    `/api/checks/by-supplier/${supplierId}/pending-summary`,
    { method: "GET" }
  );
}

export async function getDocumentPendingChecksApi(
  documentType: "sales_invoice" | "sales_quote" | "purchase_invoice" | "purchase_quote",
  invoiceId: number
) {
  return apiFetch<DocumentPendingChecksResponse>(
    `/api/checks/by-document/${documentType}/${invoiceId}/pending`,
    { method: "GET" }
  );
}

export async function registerReceivedCheckApi(
  clientId: number,
  data: RegisterReceivedCheckInput
) {
  return apiFetch<Check>(`/api/checks/by-client/${clientId}`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function registerIssuedCheckApi(
  supplierId: number,
  data: RegisterIssuedCheckInput
) {
  return apiFetch<Check>(`/api/checks/by-supplier/${supplierId}`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function depositCheckApi(checkId: number) {
  return apiFetch<Check>(`/api/checks/${checkId}/deposit`, { method: "POST" });
}

export async function creditCheckApi(checkId: number) {
  return apiFetch<Check>(`/api/checks/${checkId}/credit`, { method: "POST" });
}

export async function rejectCheckApi(checkId: number, data: RejectCheckInput) {
  return apiFetch<Check>(`/api/checks/${checkId}/reject`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}
