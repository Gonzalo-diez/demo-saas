import { create } from "zustand";
import type { PlatformAdmin } from "@/features/platform/types";

type PlatformAuthState = {
  admin: PlatformAdmin | null;
  setAdmin: (admin: PlatformAdmin | null) => void;
  clearAdmin: () => void;
};

export const usePlatformAuthStore = create<PlatformAuthState>((set) => ({
  admin: null,
  setAdmin: (admin) => set({ admin }),
  clearAdmin: () => set({ admin: null }),
}));
