"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
  getPlatformMeApi,
  platformLoginApi,
  platformLogoutApi,
} from "@/features/platform/apis/platform-auth-api";
import { usePlatformAuthStore } from "@/features/platform/store/platform-auth-store";
import type { PlatformLoginInput } from "@/features/platform/types";

export const PLATFORM_SESSION_KEY = ["platform", "me"] as const;

export function usePlatformSession() {
  const setAdmin = usePlatformAuthStore((state) => state.setAdmin);

  return useQuery({
    queryKey: PLATFORM_SESSION_KEY,
    queryFn: async () => {
      const admin = await getPlatformMeApi();
      setAdmin(admin);
      return admin;
    },
    retry: false,
    staleTime: 1000 * 60 * 5,
  });
}

export function usePlatformLogin() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const setAdmin = usePlatformAuthStore((state) => state.setAdmin);

  return useMutation({
    mutationFn: (data: PlatformLoginInput) => platformLoginApi(data),
    onSuccess: async (admin) => {
      setAdmin(admin);
      queryClient.setQueryData(PLATFORM_SESSION_KEY, admin);
      router.replace("/platform/tenants");
    },
  });
}

export function usePlatformLogout() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const clearAdmin = usePlatformAuthStore((state) => state.clearAdmin);

  const finish = () => {
    clearAdmin();
    queryClient.clear();
    router.replace("/platform/login");
  };

  return useMutation({
    mutationFn: platformLogoutApi,
    onSuccess: finish,
    onError: finish,
  });
}
