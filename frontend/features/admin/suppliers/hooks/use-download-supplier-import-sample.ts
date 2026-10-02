"use client";

import { useMutation } from "@tanstack/react-query";
import { downloadSupplierImportSampleApi } from "@/features/admin/suppliers/apis/suppliers-api";

export function useDownloadSupplierImportSample() {
  return useMutation({
    mutationFn: () => downloadSupplierImportSampleApi(),
  });
}