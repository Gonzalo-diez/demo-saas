"use client";

import { useQuery } from "@tanstack/react-query";
import { getCategoriesApi } from "@/features/admin/categories/apis/categories-api";
import type { CategoriesQueryParams } from "@/features/admin/categories/types";

export const CATEGORIES_QUERY_KEY = ["categories"] as const;

export function useCategories(params: CategoriesQueryParams = {}) {
  return useQuery({
    queryKey: [...CATEGORIES_QUERY_KEY, params],
    queryFn: () => getCategoriesApi(params),
    staleTime: 30_000,
    placeholderData: (previousData) => previousData,
  });
}
