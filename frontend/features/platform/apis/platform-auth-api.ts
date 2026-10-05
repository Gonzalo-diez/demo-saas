import { apiFetch } from "@/lib/fetcher";
import type { PlatformAdmin, PlatformLoginInput } from "@/features/platform/types";

export async function platformLoginApi(data: PlatformLoginInput) {
  return apiFetch<PlatformAdmin>("/api/admin/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getPlatformMeApi() {
  return apiFetch<PlatformAdmin>("/api/admin/me", { method: "GET" });
}

export async function platformLogoutApi() {
  return apiFetch<{ message: string }>("/api/admin/logout", { method: "POST" });
}
