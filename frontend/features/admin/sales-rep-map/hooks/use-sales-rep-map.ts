import { useQuery } from "@tanstack/react-query";
import { getSalesRepMap } from "../apis/map-api";
import type { MapFilters } from "../types";

// El filtro geográfico es complementario: o están los tres campos
// (lat, lng, radius_km) o no está ninguno. Mientras el usuario está
// completando solo uno o dos, no disparamos la consulta (evita pedir
// al backend con datos a medio completar).
function isGeoFilterUsable(filters: MapFilters): boolean {
  const fieldsPresent = [
    filters.lat !== undefined,
    filters.lng !== undefined,
    filters.radius_km !== undefined,
  ];

  const allPresent = fieldsPresent.every(Boolean);
  const nonePresent = fieldsPresent.every((present) => !present);

  return allPresent || nonePresent;
}

export function useSalesRepMap(filters: MapFilters) {
  return useQuery({
    queryKey: ["sales-rep-map", filters],
    queryFn: () =>
      getSalesRepMap({
        lat: filters.lat,
        lng: filters.lng,
        radius_km: filters.radius_km,
        search: filters.search,
        isActive: filters.isActive,
      }),
    enabled: isGeoFilterUsable(filters),
    placeholderData: (previousData) => previousData,
  });
}
