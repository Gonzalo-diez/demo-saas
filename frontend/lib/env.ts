export const env = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  siteUrl: process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
  // Distribuidora a usar cuando el navegador todavía no eligió ninguna (opcional).
  defaultTenantSlug: process.env.NEXT_PUBLIC_DEFAULT_TENANT_SLUG ?? "",
  // Sufijo con el que el panel de plataforma propone el dominio de una distribuidora nueva
  // (<codigo><sufijo>). En desarrollo es ".localhost": esos dominios resuelven a tu
  // máquina sin tocar el archivo hosts, así cada distribuidora tiene su URL local.
  // En producción no se propone nada (cada distribuidora trae su dominio real).
  tenantDomainSuffix:
    process.env.NEXT_PUBLIC_TENANT_DOMAIN_SUFFIX ??
    (process.env.NODE_ENV === "production" ? "" : ".localhost"),
}