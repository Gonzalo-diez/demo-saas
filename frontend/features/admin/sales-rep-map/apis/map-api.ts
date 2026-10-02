import { apiFetch } from "@/lib/fetcher";
import { salesRepMapResponseSchema } from "../schemas/map-schema";

type GetSalesRepMapParams = {
  lat?: number;
  lng?: number;
  radius_km?: number;
  search?: string;
  isActive?: boolean;
};

function buildSalesRepMapQuery(params: GetSalesRepMapParams) {
  const searchParams = new URLSearchParams();

  // El filtro geográfico es opcional/complementario: solo se manda
  // si el usuario completó lat, lng y radius_km.
  if (params.lat !== undefined) {
    searchParams.set("lat", String(params.lat));
  }

  if (params.lng !== undefined) {
    searchParams.set("lng", String(params.lng));
  }

  if (params.radius_km !== undefined) {
    searchParams.set("radius_km", String(params.radius_km));
  }

  if (params.search) {
    searchParams.set("search", params.search);
  }

  if (params.isActive !== undefined) {
    searchParams.set("is_active", String(params.isActive));
  }

  const query = searchParams.toString();

  return `/api/sales-reps/map${query ? `?${query}` : ""}`;
}

export async function getSalesRepMap(params: GetSalesRepMapParams) {
  const response = await apiFetch<unknown>(buildSalesRepMapQuery(params), {
    method: "GET",
  });

  return salesRepMapResponseSchema.parse(response);
}
