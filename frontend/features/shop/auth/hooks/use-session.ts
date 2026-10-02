"use client";

import { useQuery } from "@tanstack/react-query";
import { getClientMeApi } from "@/features/shop/auth/apis/auth-api";
import { useClientAuthStore } from "@/features/shop/auth/store/auth-store";

export function useClientSession() {
  const setClient = useClientAuthStore((state) => state.setClient);
  const clearClient = useClientAuthStore((state) => state.clearClient);

  return useQuery({
    queryKey: ["shop-auth", "me"],
    queryFn: async () => {
      try {
        const client = await getClientMeApi();
        setClient(client);
        return client;
      } catch (error) {
        clearClient();
        throw error;
      }
    },
    retry: false,
    staleTime: 1000 * 60 * 5,
    throwOnError: false,
  });
}