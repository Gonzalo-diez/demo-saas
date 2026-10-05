import { env } from "@/lib/env"

/**
 * URL base de la API.
 *
 * La cookie de sesión la pone el backend con SameSite=Lax, y el navegador la descarta (o no la
 * manda) cuando la tienda y la API están en SITIOS distintos. Con las URLs locales de cada
 * distribuidora (distri-norte.localhost:3000) y la API en localhost:8000 pasa justo eso: el
 * login responde 200 pero la cookie no queda y /sales-reps/me da 401.
 *
 * Por eso, en un dominio *.localhost se llama a /api en el mismo dominio de la tienda y Next lo
 * reenvía al backend (rewrites de next.config.ts). En el resto de los casos se respeta
 * NEXT_PUBLIC_API_URL.
 */
export function getApiUrl(): string {
  const configured = env.apiUrl

  if (typeof window === "undefined" || !configured) return configured

  try {
    const apiHost = new URL(configured).hostname
    const pageHost = window.location.hostname
    const isTenantDevDomain = pageHost.endsWith(".localhost")

    if (isTenantDevDomain && apiHost !== pageHost) return ""
  } catch {
    // NEXT_PUBLIC_API_URL no es una URL absoluta (ej. "/api-backend"): se usa tal cual.
  }

  return configured
}
