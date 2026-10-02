"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { commitProductsImportApi } from "@/features/admin/products/apis/products-api";
import type { ProductImportCommitRequest } from "@/features/admin/products/types";

export function useProductsImportCommit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ProductImportCommitRequest) =>
      commitProductsImportApi(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
    },
  });
}