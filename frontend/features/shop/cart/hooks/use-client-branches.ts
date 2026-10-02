import { useQuery } from "@tanstack/react-query";
import { clientBranchesApi } from "@/features/shop/cart/apis/client-branches-api";
import { useClientAuthStore } from "@/features/shop/auth/store/auth-store";

export function useClientBranches() {
  const isAuthenticated = useClientAuthStore((s) => s.isAuthenticated);

  return useQuery({
    queryKey: ["client-branches", "me"],
    queryFn: () => clientBranchesApi.listMine(),
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
  });
}