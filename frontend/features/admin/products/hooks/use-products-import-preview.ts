"use client";

import { useMutation } from "@tanstack/react-query";
import { previewProductsImportApi } from "@/features/admin/products/apis/products-api";

export function useProductsImportPreview() {
  return useMutation({
    mutationFn: (file: File) => previewProductsImportApi(file),
  });
}