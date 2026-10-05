import { apiFetch } from "@/lib/fetcher";
import type { ShopCategoriesResponse } from "@/features/shop/categories/types";

export async function getShopCategoriesApi() {
  return apiFetch<ShopCategoriesResponse>("/api/categories/", { method: "GET" });
}
