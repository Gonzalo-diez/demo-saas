import { useQuery } from "@tanstack/react-query";
import { getClientsMap } from "../apis/map-api";
import type { MapFilters } from "../types";

export function useClientsMap(filters?: MapFilters) {
  return useQuery({
    queryKey: ["clients-map", filters],
    queryFn: () =>
      getClientsMap({
        salesRepId: filters?.salesRepId,
        search: filters?.search,
        isActive: filters?.isActive,
      }),
  });
}