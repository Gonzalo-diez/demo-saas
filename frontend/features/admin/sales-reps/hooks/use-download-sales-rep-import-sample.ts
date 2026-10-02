"use client";

import { useMutation } from "@tanstack/react-query";
import { downloadSalesRepImportSampleApi } from "@/features/admin/sales-reps/apis/sales-reps-api";

export function useDownloadSalesRepImportSample() {
  return useMutation({
    mutationFn: () => downloadSalesRepImportSampleApi(),
  });
}