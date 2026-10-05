import { apiFetch } from "@/lib/fetcher";
import type { TenantPublic } from "@/features/tenant/types";

/** Datos públicos de una distribuidora (nombre y logo) por su código. */
export async function getTenantPublicApi(slug: string) {
  return apiFetch<TenantPublic>(
    `/api/tenants/slug/${encodeURIComponent(slug)}`,
    { method: "GET" },
  );
}

/**
 * Distribuidora dueña de un dominio (el host con el que el cliente abrió la
 * tienda). `tienda.x.com` y `www.tienda.x.com` llegan a la misma.
 */
export async function getTenantByDomainApi(host: string) {
  return apiFetch<TenantPublic>(
    `/api/tenants/by-domain/${encodeURIComponent(host)}`,
    { method: "GET" },
  );
}
