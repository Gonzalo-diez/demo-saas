"use client";

import { useMutation } from "@tanstack/react-query";
import { downloadClientImportSampleApi } from "@/features/admin/clients/apis/clients-api";

export function useDownloadClientImportSample() {
  return useMutation({
    mutationFn: () => downloadClientImportSampleApi(),
  });
}