"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
  loginClientApi,
  logoutClientApi,
} from "@/features/shop/auth/apis/auth-api";
import { useClientAuthStore } from "@/features/shop/auth/store/auth-store";
import type { ClientLoginInput } from "@/features/shop/auth/types";

export function useClientLogin(redirectTo: string = "/catalogo") {
  const router = useRouter();
  const queryClient = useQueryClient();
  const setClient = useClientAuthStore((state) => state.setClient);

  return useMutation({
    mutationFn: async (data: ClientLoginInput) => {
      return loginClientApi(data);
    },
    onSuccess: async (client) => {
      setClient(client);
      await queryClient.invalidateQueries({ queryKey: ["shop-auth"] });
      router.replace(redirectTo);
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