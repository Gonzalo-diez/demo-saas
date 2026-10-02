"use client";

import { useMutation } from "@tanstack/react-query";
import { previewSalesRepImportApi } from "@/features/admin/sales-reps/apis/sales-reps-api";

export function useSalesRepsImportPreview() {
    return useMutation({
        mutationFn: (file: File) => previewSalesRepImportApi(file)
    });
}