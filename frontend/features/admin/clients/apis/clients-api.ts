import { apiFetch, apiFetchBlob } from "@/lib/fetcher";
import {
  ClientImportCommitRequest,
  ClientImportCommitResponse,
  ClientImportPreviewResponse,
  type Client,
  type ClientMapResponse,
  type ClientsQueryParams,
  type ClientsResponse,
  type CreateClientInput,
  type UpdateClientInput,
} from "@/features/admin/clients/types";

function buildClientsQuery(params: ClientsQueryParams = {}) {
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

  if (params.sort) {
    searchParams.set("sort", params.sort);
  }

  if (params.sales_rep_id) {
    searchParams.set("sales_rep_id", String(params.sales_rep_id));
  }

  const query = searchParams.toString();
  return query ? `/api/clients?${query}` : "/api/clients";
}

export async function getClientsApi(params: ClientsQueryParams = {}) {
  return apiFetch<ClientsResponse>(buildClientsQuery(params), {
    method: "GET",
  });
}

export async function getClientApi(clientId: number) {
  return apiFetch<Client>(`/api/clients/${clientId}`, {
    method: "GET",
  });
}

export async function createClientApi(data: CreateClientInput) {
  return apiFetch<Client>("/api/clients", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function previewImportClientsApi(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  return apiFetch<ClientImportPreviewResponse>("/api/clients/import/preview", {
    method: "POST",
    body: formData,
  });
}

export async function commitClientsImportApi(
  data: ClientImportCommitRequest
) {
  return apiFetch<ClientImportCommitResponse>("/api/clients/import/commit", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function commitClientsImportFileApi(file: File, mode: string = "upsert") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("mode", mode);

  return apiFetch<ClientImportCommitResponse>("/api/clients/import/commit-file", {
    method: "POST",
    body: formData,
  });
}

export async function downloadClientImportSampleApi(): Promise<Blob> {
  return apiFetchBlob("/api/clients/import/sample-excel", {
    method: "GET",
  });
}

export async function updateClientApi(clientId: number, data: UpdateClientInput) {
  return apiFetch<Client>(`/api/clients/${clientId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function activateClientApi(clientId: number) {
  return apiFetch<Client>(`/api/clients/${clientId}/activate`, {
    method: "PATCH",
  });
}

export async function deactivateClientApi(clientId: number) {
  return apiFetch<Client>(`/api/clients/${clientId}/deactivate`, {
    method: "PATCH",
  });
}

export async function getClientsMapApi() {
  return apiFetch<ClientMapResponse>("/api/clients/map", {
    method: "GET",
  });
}