"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { loginApi, logoutApi } from "@/features/admin/auth/apis/auth-api";
import { useAuthStore } from "@/features/admin/auth/store/auth-store";
import { useTenantStore } from "@/features/tenant/store/tenant-store";
import type { LoginSchema } from "@/features/admin/auth/schemas/login-schema";

export function useLogin() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const setUser = useAuthStore((state) => state.setUser);
  const setTenantSlug = useTenantStore((state) => state.setSlug);

  return useMutation({
    mutationFn: async ({ tenant_slug, ...credentials }: LoginSchema) => {
      // En el dominio de la distribuidora viaja el dominio (X-Tenant-Domain); si no
      // (localhost / dominio de la plataforma) viaja el código elegido (X-Tenant-Slug).
      if (!useTenantStore.getState().hostTenant) setTenantSlug(tenant_slug);
      return loginApi(credentials);
    },
    onSuccess: async (user) => {
      setUser(user);
      await queryClient.invalidateQueries({ queryKey: ["auth"] });
      router.replace("/admin/dashboard");
    },
  });
}

export function useLogout() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const clearUser = useAuthStore((state) => state.clearUser);

  return useMutation({
    mutationFn: logoutApi,
    onSuccess: async () => {
      clearUser();
      queryClient.clear();
      router.replace("/login");
    },
    onError: async () => {
      clearUser();
      queryClient.clear();
      router.replace("/login");
    },
  });
}