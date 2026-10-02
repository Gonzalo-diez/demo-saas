"use client";

import { useQuery } from "@tanstack/react-query";
import { getClientsApi } from "@/features/admin/clients/apis/clients-api";
import type { ClientsQueryParams } from "@/features/admin/clients/types";

export function useClients(params: ClientsQueryParams) {
  return useQuery({
    queryKey: ["clients", params],
    queryFn: () => getClientsApi(params),
    placeholderData: (previousData) => previousData,
  });
}