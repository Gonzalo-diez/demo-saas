"use client";

import { useQuery } from "@tanstack/react-query";
import { getMeApi } from "@/features/admin/auth/apis/auth-api";
import { useAuthStore } from "@/features/admin/auth/store/auth-store";

export function useSession() {
  const setUser = useAuthStore((state) => state.setUser);
  const clearUser = useAuthStore((state) => state.clearUser);

  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      const user = await getMeApi();
      setUser(user);
      return user;
    },
    retry: false,
    staleTime: 1000 * 60 * 5,
    throwOnError: false,
  });
}