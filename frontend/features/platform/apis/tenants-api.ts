import { apiFetch } from "@/lib/fetcher";
import type {
  CreateTenantInput,
  PaginatedTenants,
  Tenant,
  TenantsQueryParams,
  UpdateTenantInput,
} from "@/features/platform/types";

export async function getTenantsApi(params: TenantsQueryParams = {}) {
  const searchParams = new URLSearchParams();
  searchParams.set("page", String(params.page ?? 1));
  searchParams.set("page_size", String(params.page_size ?? 20));
  if (params.search) searchParams.set("search", params.search);
  if (params.is_active !== undefined) searchParams.set("is_active", String(params.is_active));
  if (params.sort) searchParams.set("sort", params.sort);

  return apiFetch<PaginatedTenants>(`/api/tenants/?${searchParams.toString()}`, {
    method: "GET",
  });
}

export async function createTenantApi(data: CreateTenantInput) {
  return apiFetch<Tenant>("/api/tenants/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateTenantApi(tenantId: number, data: UpdateTenantInput) {
  return apiFetch<Tenant>(`/api/tenants/${tenantId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function setTenantActiveApi(tenantId: number, active: boolean) {
  return apiFetch<Tenant>(`/api/tenants/${tenantId}/${active ? "activate" : "deactivate"}`, {
    method: "PATCH",
  });
}
