import { apiFetch } from "@/lib/fetcher";
import type {
  CreateProductPurchaseInput,
  ProductPurchase,
  ProductPurchaseListResponse,
} from "@/features/admin/products/purchase-types";

export async function getProductPurchasesApi(
  productId: number,
  params: { page?: number; pageSize?: number } = {},
) {
  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.pageSize) query.set("page_size", String(params.pageSize));
  const qs = query.toString();

  return apiFetch<ProductPurchaseListResponse>(
    `/api/products/${productId}/purchases/${qs ? `?${qs}` : ""}`,
    { method: "GET" },
  );
}

export async function createProductPurchaseApi(
  productId: number,
  data: CreateProductPurchaseInput,
) {
  return apiFetch<ProductPurchase>(`/api/products/${productId}/purchases/`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}
