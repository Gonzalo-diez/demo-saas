"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { loginApi, logoutApi } from "@/features/admin/auth/apis/auth-api";
import { useAuthStore } from "@/features/admin/auth/store/auth-store";
import type { LoginInput } from "@/features/admin/auth/types";

export function useLogin() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const setUser = useAuthStore((state) => state.setUser);

  return useMutation({
    mutationFn: async (data: LoginInput) => {
      return loginApi(data);
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