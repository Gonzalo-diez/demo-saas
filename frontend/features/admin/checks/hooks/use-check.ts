"use client";

import { useQuery } from "@tanstack/react-query";
import { getCheckApi } from "@/features/admin/checks/apis/check-api";

export function useCheck(checkId: number | null) {
  return useQuery({
    queryKey: ["check", checkId],
    queryFn: () => {
      if (!checkId) {
        throw new Error("checkId es requerido");
      }
      return getCheckApi(checkId);
    },
    enabled: !!checkId,
  });
}
