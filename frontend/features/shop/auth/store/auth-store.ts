import { create } from "zustand";
import type { ClientUser } from "@/features/shop/auth/types";

type ClientAuthState = {
  client: ClientUser | null;
  isAuthenticated: boolean;
  setClient: (client: ClientUser | null) => void;
  clearClient: () => void;
};

export const useClientAuthStore = create<ClientAuthState>((set) => ({
  client: null,
  isAuthenticated: false,
  setClient: (client) =>
    set({
      client,
      isAuthenticated: !!client,
    }),
  clearClient: () =>
    set({
      client: null,
      isAuthenticated: false,
    }),
}));