"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
  loginClientApi,
  logoutClientApi,
  registerClientApi,
} from "@/features/shop/auth/apis/auth-api";
import { useClientAuthStore } from "@/features/shop/auth/store/auth-store";
import { useTenantStore } from "@/features/tenant/store/tenant-store";
import type { ClientLoginSchema } from "@/features/shop/auth/schemas/login-schema";
import type { ClientRegisterSchema } from "@/features/shop/auth/schemas/register-schema";

/**
 * Login del cliente de la tienda. `redirectTo` es a dónde ir al terminar; con `null`
 * se queda en la misma página (el checkout, donde el formulario aparece solo).
 */
export function useClientLogin(redirectTo: string | null = "/catalogo") {
  const router = useRouter();
  const queryClient = useQueryClient();
  const setClient = useClientAuthStore((state) => state.setClient);
  const setTenantSlug = useTenantStore((state) => state.setSlug);

  return useMutation({
    mutationFn: async ({ tenant_slug, ...credentials }: ClientLoginSchema) => {
      // En el dominio de la distribuidora viaja el dominio (X-Tenant-Domain); si no
      // (localhost / dominio de la plataforma) viaja el código elegido (X-Tenant-Slug).
      if (!useTenantStore.getState().hostTenant) setTenantSlug(tenant_slug);
      return loginClientApi(credentials);
    },
    onSuccess: async (client) => {
      setClient(client);
      await queryClient.invalidateQueries({ queryKey: ["shop-auth"] });
      if (redirectTo) router.replace(redirectTo);
    },
  });
}

/**
 * Registro del cliente de la tienda. Se usa recién al finalizar una compra (o desde
 * /ingresar): crea la cuenta en la distribuidora del dominio y deja la sesión iniciada.
 */
export function useClientRegister(redirectTo: string | null = null) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const setClient = useClientAuthStore((state) => state.setClient);
  const setTenantSlug = useTenantStore((state) => state.setSlug);

  return useMutation({
    mutationFn: async ({ tenant_slug, ...data }: ClientRegisterSchema) => {
      if (!useTenantStore.getState().hostTenant) setTenantSlug(tenant_slug);
      return registerClientApi({
        name: data.name,
        email: data.email,
        password: data.password,
        phone: data.phone,
        client_type: data.client_type,
        ...(data.tax_id ? { tax_id: data.tax_id } : {}),
      });
    },
    onSuccess: async (client) => {
      setClient(client);
      await queryClient.invalidateQueries({ queryKey: ["shop-auth"] });
      if (redirectTo) router.replace(redirectTo);
    },
  });
}

export function useClientLogout() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const clearClient = useClientAuthStore((state) => state.clearClient);

  return useMutation({
    mutationFn: logoutClientApi,
    onSuccess: async () => {
      clearClient();
      queryClient.clear();
      router.replace("/ingresar");
    },
    onError: async () => {
      clearClient();
      queryClient.clear();
      router.replace("/ingresar");
    },
  });
}