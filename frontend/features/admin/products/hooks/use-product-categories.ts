"use client";

import { useQuery } from "@tanstack/react-query";
import { getProductCategoriesApi } from "@/features/admin/products/apis/products-api";

export const PRODUCT_CATEGORIES_QUERY_KEY = ["product-categories"] as const;

export function useProductCategories() {
  return useQuery({
    queryKey: PRODUCT_CATEGORIES_QUERY_KEY,
    queryFn: getProductCategoriesApi,
    staleTime: 60_000,
  });
}
