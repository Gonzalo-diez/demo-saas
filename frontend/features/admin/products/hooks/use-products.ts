"use client";

import { useQuery } from "@tanstack/react-query";
import { getProductsApi } from "@/features/admin/products/apis/products-api";
import type { ProductSort, ProductStatusFilter } from "@/features/admin/products/types";

type UseProductsParams = {
  page: number;
  page_size: number;
  search: string;
  status: ProductStatusFilter;
  brand: string;
  sort: ProductSort;
};

export function useProducts(params: UseProductsParams) {
  return useQuery({
    queryKey: ["products", params],
    queryFn: () => getProductsApi(params),
    placeholderData: (previousData) => previousData,
  });
}