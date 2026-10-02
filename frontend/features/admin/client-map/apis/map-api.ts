import { apiFetch } from "@/lib/fetcher";
import { clientsMapResponseSchema } from "../schemas/map-schemas";

type GetClientsMapParams = {
  salesRepId?: number;
  search?: string;
  isActive?: boolean;
};

function buildClientsMapQuery(params: GetClientsMapParams = {}) {
  const searchParams = new URLSearchParams();

  if (params.salesRepId !== undefined) {
    searchParams.set("sales_rep_id", String(params.salesRepId));
  }

  if (params.search) {
    searchParams.set("search", params.search);
  }

  if (params.isActive !== undefined) {
    searchParams.set("is_active", String(params.isActive));
  }

  const queryString = searchParams.toString();
  return queryString ? `/api/clients/map?${queryString}` : "/api/clients/map";
}

export async function getClientsMap(params: GetClientsMapParams = {}) {
  const response = await apiFetch<unknown>(buildClientsMapQuery(params), {
    method: "GET",
  });

  return clientsMapResponseSchema.parse(response);
}