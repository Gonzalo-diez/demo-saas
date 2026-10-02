"use client";

import { useMutation } from "@tanstack/react-query";
import { previewImportClientsApi } from "@/features/admin/clients/apis/clients-api";

export function useClientsImportPreview() {
    return useMutation({
        mutationFn: (file: File) => previewImportClientsApi(file)
    });
}