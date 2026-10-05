import { apiFetch } from "@/lib/fetcher";
import type {
  CreatePlatformAdminInput,
  PlatformAdmin,
  UpdatePlatformAdminInput,
} from "@/features/platform/types";

export async function getPlatformAdminsApi() {
  return apiFetch<PlatformAdmin[]>("/api/admin/users", { method: "GET" });
}

export async function createPlatformAdminApi(data: CreatePlatformAdminInput) {
  return apiFetch<PlatformAdmin>("/api/admin/users", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updatePlatformAdminApi(adminId: number, data: UpdatePlatformAdminInput) {
  return apiFetch<PlatformAdmin>(`/api/admin/users/${adminId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deletePlatformAdminApi(adminId: number) {
  return apiFetch<{ message: string }>(`/api/admin/users/${adminId}`, { method: "DELETE" });
}
