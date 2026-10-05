import { env } from "@/lib/env";

const STORAGE_KEY = "tenant_slug";

export function normalizeTenantSlug(value: string | null | undefined): string {
  return (value ?? "").trim().toLowerCase();
}

/**
 * Host (sin puerto) con el que se abrió la app, en minúsculas. La tienda de cada
 * distribuidora se identifica por este host: `tienda.distri-oeste.com`,
 * `distri-oeste.localhost`, etc. Solo existe en el navegador.
 */
export function getCurrentHost(): string | null {
  if (typeof window === "undefined") return null;
  return window.location.hostname.trim().toLowerCase() || null;
}

/** `localhost` / IP: no pertenecen a ninguna distribuidora, ahí se elige por código. */
export function isBareLocalHost(host: string | null | undefined): boolean {
  return (
    host === "localhost" ||
    host === "127.0.0.1" ||
    host === "[::1]" ||
    host === "::1"
  );
}

/**
 * Código (slug) de la distribuidora elegida A MANO en este navegador: el campo
 * "Distribuidora" del login o `?tenant=`. Solo se usa cuando el dominio no
 * identifica a ninguna distribuidora (localhost o el dominio de la plataforma).
 */
export function getStoredTenantSlug(): string | null {
  if (typeof window === "undefined") return null;
  try {
    const stored = normalizeTenantSlug(window.localStorage.getItem(STORAGE_KEY));
    if (stored) return stored;
  } catch {
    // localStorage bloqueado: seguimos con el valor por defecto.
  }
  // La distribuidora por defecto del .env es solo para desarrollo en localhost:
  // en un dominio real mandaría el dominio, no un código fijo.
  if (isBareLocalHost(getCurrentHost())) {
    return normalizeTenantSlug(env.defaultTenantSlug) || null;
  }
  return null;
}

export function setStoredTenantSlug(slug: string | null) {
  if (typeof window === "undefined") return;
  try {
    const clean = normalizeTenantSlug(slug);
    if (clean) window.localStorage.setItem(STORAGE_KEY, clean);
    else window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignoramos errores de almacenamiento
  }
}
