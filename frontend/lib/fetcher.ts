import { getApiUrl } from "@/lib/api";
import {
  getCurrentHost,
  getStoredTenantSlug,
  isBareLocalHost,
} from "@/lib/tenant-storage";
import { useTenantStore } from "@/features/tenant/store/tenant-store";

type FetchOptions = RequestInit;

/**
 * Headers que identifican la distribuidora. El backend los usa solo en endpoints
 * sin sesión (catálogo público, login, registro, tracking); con sesión manda el
 * tenant del token.
 *
 * - X-Tenant-Domain: el host con el que se abrió la tienda (tienda.distri-oeste.com).
 *   Es lo que identifica a la distribuidora de un visitante.
 * - X-Tenant-Slug: el código elegido a mano. Solo se manda si el dominio NO
 *   identifica a ninguna distribuidora (localhost o dominio de la plataforma),
 *   porque en el backend el código tiene prioridad sobre el dominio.
 */
export function tenantHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};

  const host = getCurrentHost();
  if (host) headers["X-Tenant-Domain"] = host;

  // El código elegido a mano solo cuenta en localhost o cuando ya se comprobó que el
  // dominio no es de ninguna distribuidora. Antes de eso NO se manda: un código viejo
  // guardado en el navegador pisaría al dominio (el backend prioriza el código).
  const { hostTenant, hostChecked } = useTenantStore.getState();
  if (!hostTenant && (hostChecked || isBareLocalHost(host))) {
    const slug = getStoredTenantSlug();
    if (slug) headers["X-Tenant-Slug"] = slug;
  }

  return headers;
}

export async function apiFetch<T>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T> {
  const isFormData = options.body instanceof FormData;

  const response = await fetch(`${getApiUrl()}${endpoint}`, {
    ...options,
    credentials: "include",
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...tenantHeaders(),
      ...(options.headers ?? {}),
    },
  });

  if (!response.ok) {
    let message = "Ocurrió un error";

    try {
      const errorData = await response.json();
      message = errorData.detail ?? message;
    } catch {}

    throw new Error(message);
  }

  if (response.status === 204) {
    return null as T;
  }

  return response.json() as Promise<T>;
}

/**
 * Variante de apiFetch para endpoints que devuelven un archivo binario
 * (Excel, PDF, etc). Devuelve el Blob listo para descargar.
 */
export async function apiFetchBlob(
  endpoint: string,
  options: FetchOptions = {}
): Promise<Blob> {
  const response = await fetch(`${getApiUrl()}${endpoint}`, {
    ...options,
    credentials: "include",
    headers: {
      ...tenantHeaders(),
      ...(options.headers ?? {}),
    },
  });

  if (!response.ok) {
    let message = "Ocurrió un error";

    try {
      const errorData = await response.json();
      message = errorData.detail ?? message;
    } catch {}

    throw new Error(message);
  }

  return response.blob();
}

/**
 * Dispara la descarga de un Blob en el navegador con el nombre indicado.
 */
export function triggerBlobDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}