"use client";

import { useMutation } from "@tanstack/react-query";
import { generateImportExcelFromPdfApi } from "@/features/admin/products/apis/products-api";

export function useImportExcelFromPdf() {
  return useMutation({
    mutationFn: (file: File) => generateImportExcelFromPdfApi(file),
  });
}