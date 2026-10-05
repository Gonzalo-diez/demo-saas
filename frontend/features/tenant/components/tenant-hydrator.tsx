"use client";

import { useEffect } from "react";
import { useTenantStore } from "@/features/tenant/store/tenant-store";
import { getTenantByDomainApi } from "@/features/tenant/apis/tenant-api";
import {
  getCurrentHost,
  getStoredTenantSlug,
  isBareLocalHost,
  normalizeTenantSlug,
} from "@/lib/tenant-storage";

/**
 * Al abrir la app decide a qué distribuidora pertenece:
 *
 * 1. Por DOMINIO: el host con el que se abrió (tienda.distri-oeste.com) se consulta
 *    en GET /api/tenants/by-domain/{host}. Si hay una distribuidora, esa es.
 * 2. Si el dominio no es de ninguna (localhost, el dominio de la plataforma), por
 *    CÓDIGO: ?tenant=mi-codigo en la URL > el último elegido en este navegador > .env.
 */
export function TenantHydrator() {
  const setSlug = useTenantStore((state) => state.setSlug);
  const setHostTenant = useTenantStore((state) => state.setHostTenant);

  useEffect(() => {
    const fromUrl = normalizeTenantSlug(
      new URLSearchParams(window.location.search).get("tenant"),
    );
    setSlug(fromUrl || getStoredTenantSlug());

    const host = getCurrentHost();
    // localhost / IP no pertenecen a ninguna distribuidora: nada que consultar.
    if (!host || isBareLocalHost(host)) {
      setHostTenant(null);
      return;
    }

    let cancelled = false;
    getTenantByDomainApi(host)
      .then((tenant) => {
        if (!cancelled) setHostTenant(tenant);
      })
      .catch(() => {
        // Dominio sin distribuidora (o API caída): seguimos con el código elegido.
        if (!cancelled) setHostTenant(null);
      });

    return () => {
      cancelled = true;
    };
  }, [setSlug, setHostTenant]);

  return null;
}
