"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { commitClientsImportApi } from "@/features/admin/clients/apis/clients-api";
import type { ClientImportCommitRequest } from "@/features/admin/clients/types";

export function useClientsImportCommit() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: ClientImportCommitRequest) =>
            commitClientsImportApi(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["clients"] });
        },
    });
}