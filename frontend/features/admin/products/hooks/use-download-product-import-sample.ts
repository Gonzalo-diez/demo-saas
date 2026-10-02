"use client";

import { useMutation } from "@tanstack/react-query";
import { downloadProductImportSampleApi } from "@/features/admin/products/apis/products-api";

export function useDownloadProductImportSample() {
  return useMutation({
    mutationFn: () => downloadProductImportSampleApi(),
  });
}