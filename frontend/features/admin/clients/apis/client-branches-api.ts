import { apiFetch } from "@/lib/fetcher";
import type {
  ClientBranch,
  CreateClientBranchInput,
  UpdateClientBranchInput,
} from "@/features/admin/clients/types";

export async function getClientBranchesApi(clientId: number) {
  return apiFetch<ClientBranch[]>(`/api/clients/${clientId}/branches`, {
    method: "GET",
  });
}

export async function createClientBranchApi(
  clientId: number,
  data: CreateClientBranchInput
) {
  return apiFetch<ClientBranch>(`/api/clients/${clientId}/branches`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateClientBranchApi(
  clientId: number,
  branchId: number,
  data: UpdateClientBranchInput
) {
  return apiFetch<ClientBranch>(`/api/clients/${clientId}/branches/${branchId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deactivateClientBranchApi(
  clientId: number,
  branchId: number
) {
  return apiFetch<ClientBranch>(
    `/api/clients/${clientId}/branches/${branchId}/deactivate`,
    {
      method: "PATCH",
    }
  );
}

export async function activateClientBranchApi(
  clientId: number,
  branchId: number
) {
  return apiFetch<ClientBranch>(
    `/api/clients/${clientId}/branches/${branchId}/activate`,
    {
      method: "PATCH",
    }
  );
}