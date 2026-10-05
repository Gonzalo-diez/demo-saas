import { create } from "zustand";
import type { TenantPublic } from "@/features/tenant/types";
import { normalizeTenantSlug, setStoredTenantSlug } from "@/lib/tenant-storage";

type TenantState = {
  /**
   * Código elegido a mano (campo del login, ?tenant= o .env en localhost).
   * null hasta que se hidrata en el cliente. Se ignora si el dominio ya
   * identifica a una distribuidora.
   */
  slug: string | null;
  setSlug: (slug: string | null) => void;

  /** Distribuidora dueña del dominio con el que se abrió la app (si hay una). */
  hostTenant: TenantPublic | null;
  /** Ya se consultó el dominio (haya o no distribuidora): evita parpadeos. */
  hostChecked: boolean;
  setHostTenant: (tenant: TenantPublic | null) => void;
};

export const useTenantStore = create<TenantState>((set) => ({
  slug: null,
  setSlug: (slug) => {
    const clean = normalizeTenantSlug(slug) || null;
    setStoredTenantSlug(clean);
    set({ slug: clean });
  },

  hostTenant: null,
  hostChecked: false,
  setHostTenant: (tenant) => {
    if (tenant) {
      // En el dominio de una distribuidora el código elegido a mano no pinta nada.
      setStoredTenantSlug(null);
      set({ hostTenant: tenant, hostChecked: true, slug: null });
    } else {
      set({ hostTenant: null, hostChecked: true });
    }
  },
}));
