import { apiFetch } from "@/lib/fetcher";
import type {
  InventoryMovementsQueryParams,
  InventoryMovementsResponse,
} from "@/features/admin/inventory-movements/types";

function buildInventoryMovementsQuery(
  params: InventoryMovementsQueryParams = {}
) {
  const searchParams = new URLSearchParams();

  searchParams.set("page", String(params.page ?? 1));
  searchParams.set("page_size", String(params.page_size ?? 10));

  if (params.product_id) {
    searchParams.set("product_id", String(params.product_id));
  }

  if (params.movement_type && params.movement_type !== "all") {
    searchParams.set("movement_type", params.movement_type);
  }

  if (params.reference_type && params.reference_type !== "all") {
    searchParams.set("reference_type", params.reference_type);
  }

  return `/api/inventory-movements?${searchParams.toString()}`;
}

export async function getInventoryMovementsApi(
  params: InventoryMovementsQueryParams = {}
) {
  return apiFetch<InventoryMovementsResponse>(
    buildInventoryMovementsQuery(params),
    {
      method: "GET",
    }
  );
}

export async function getProductInventoryMovementsApi(
  productId: number,
  page = 1,
  pageSize = 20
) {
  const searchParams = new URLSearchParams();
  searchParams.set("page", String(page));
  searchParams.set("page_size", String(pageSize));

  return apiFetch<InventoryMovementsResponse>(
    `/api/products/${productId}/inventory-movements?${searchParams.toString()}`,
    {
      method: "GET",
    }
  );
}