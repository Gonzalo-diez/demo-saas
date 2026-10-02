"use client";

import { useQuery } from "@tanstack/react-query";
import { getChecksApi } from "@/features/admin/checks/apis/check-api";
import type { ChecksQueryParams } from "@/features/admin/checks/types";

export function useChecks(params: ChecksQueryParams) {
  return useQuery({
    queryKey: ["checks", params],
    queryFn: () => getChecksApi(params),
    placeholderData: (previousData) => previousData,
  });
}
