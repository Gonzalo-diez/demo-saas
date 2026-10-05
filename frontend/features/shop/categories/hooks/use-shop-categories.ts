"use client";

import { useQuery } from "@tanstack/react-query";
import { getShopCategoriesApi } from "@/features/shop/categories/apis/shop-categories-api";

export const SHOP_CATEGORIES_QUERY_KEY = ["shop-categories"] as const;

export function useShopCategories() {
  return useQuery({
    queryKey: SHOP_CATEGORIES_QUERY_KEY,
    queryFn: getShopCategoriesApi,
    staleTime: 1000 * 60,
  });
}
