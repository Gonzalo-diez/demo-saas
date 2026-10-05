"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getTenantPublicApi } from "@/features/tenant/apis/tenant-api";
import { useTenantStore } from "@/features/tenant/store/tenant-store";
import { FALLBACK_TENANT_NAME } from "@/constants/brand";
import { normalizeTenantSlug } from "@/lib/tenant-storage";

function initialsOf(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  const letters = parts.length > 1 ? parts[0][0] + parts[1][0] : name.trim().slice(0, 2);
  return (letters || "D").toUpperCase();
}

/**
 * Nombre, logo e iniciales de la distribuidora actual: la dueña del dominio con el
 * que se abrió la app o, si el dominio no es de ninguna, la elegida por código.
 */
export function useTenantBranding() {
  const slug = useTenantStore((state) => state.slug);
  const hostTenant = useTenantStore((state) => state.hostTenant);
  const hostChecked = useTenantStore((state) => state.hostChecked);

  const query = useQuery({
    queryKey: ["tenant", "public", slug],
    queryFn: () => getTenantPublicApi(slug as string),
    // Solo hace falta pedirla por código si el dominio no la resolvió.
    enabled: hostChecked && !hostTenant && !!slug,
    staleTime: 1000 * 60 * 5,
  });

  const tenant = hostTenant ?? query.data ?? null;
  const name = tenant?.name ?? FALLBACK_TENANT_NAME;

  return {
    slug: tenant?.slug ?? slug,
    name,
    logoUrl: tenant?.logo_url ?? null,
    initials: initialsOf(name),
    isLoading: !hostChecked || query.isLoading,
    exists: !!tenant,
    /** true cuando la distribuidora salió del dominio (no hay que pedir el código). */
    fromDomain: !!hostTenant,
  };
}

/** Busca la distribuidora que se está tipeando en el login (con debounce). */
export function useTenantPreview(rawSlug: string) {
  const [debounced, setDebounced] = useState(normalizeTenantSlug(rawSlug));

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(normalizeTenantSlug(rawSlug)), 400);
    return () => clearTimeout(timer);
  }, [rawSlug]);

  const query = useQuery({
    queryKey: ["tenant", "public", debounced],
    queryFn: () => getTenantPublicApi(debounced),
    enabled: debounced.length > 0,
    staleTime: 1000 * 60 * 5,
  });

  return {
    tenant: query.data ?? null,
    isChecking: debounced.length > 0 && query.isFetching,
    notFound: debounced.length > 0 && query.isError,
  };
}
