/** Convierte un nombre en un código válido para la URL/login ("Distri Oeste" -> "distri-oeste"). */
export function slugify(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, "")
    .replace(/[\s_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export const SLUG_REGEX = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

/**
 * Host de un dominio o URL, igual que lo guarda el backend: sin esquema, puerto,
 * path ni credenciales, en minúsculas. Devuelve "" si no se puede interpretar.
 *   "https://Tienda.X.com:8443/inicio" -> "tienda.x.com"
 */
export function extractHost(value: string): string {
  const raw = value.trim().toLowerCase();
  if (!raw) return "";
  try {
    const url = new URL(raw.includes("://") ? raw : `//${raw}`, "http://placeholder.invalid");
    return url.hostname.replace(/\.$/, "");
  } catch {
    return "";
  }
}

/** Dominio válido (letras, números, guiones y puntos; no IP). Espeja las reglas del backend. */
const DOMAIN_LABEL = /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/;
export function isValidDomainHost(host: string): boolean {
  if (!host || host.length > 253) return false;
  if (/^\d{1,3}(\.\d{1,3}){3}$/.test(host) || host.includes(":")) return false; // IP
  return host.split(".").every((label) => DOMAIN_LABEL.test(label));
}
