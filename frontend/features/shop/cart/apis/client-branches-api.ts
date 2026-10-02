import { apiFetch } from "@/lib/fetcher";
import type { ClientBranch } from "@/features/shop/cart/types";

export const clientBranchesApi = {
  listMine: async (): Promise<ClientBranch[]> => {
    return apiFetch<ClientBranch[]>("/api/clients/me/branches");
  },
};