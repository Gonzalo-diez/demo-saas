"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { commitSalesRepImportApi } from "@/features/admin/sales-reps/apis/sales-reps-api";
import type { SalesRepImportCommitRequest } from "@/features/admin/sales-reps/types";

export function useSalesRepsImportCommit() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: SalesRepImportCommitRequest) =>
            commitSalesRepImportApi(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["sales-reps"] });
        },
    });
}