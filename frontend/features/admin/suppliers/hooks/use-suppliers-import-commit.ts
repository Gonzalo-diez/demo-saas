"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { commitSuppliersImportApi } from "@/features/admin/suppliers/apis/suppliers-api";
import type { SupplierImportCommitRequest } from "@/features/admin/suppliers/types";

export function useSuppliersImportCommit() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: SupplierImportCommitRequest) =>
            commitSuppliersImportApi(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["suppliers"] })
        },
    });
}