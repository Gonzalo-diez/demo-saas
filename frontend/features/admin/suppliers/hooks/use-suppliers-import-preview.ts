"use client";

import { useMutation } from "@tanstack/react-query";
import { previewSuppliersImportApi } from "@/features/admin/suppliers/apis/suppliers-api";

export function useSuppliersImportPreview() {
    return useMutation({
        mutationFn: (file: File) => previewSuppliersImportApi(file)
    });
}