"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createClientApi } from "@/features/admin/clients/apis/clients-api";
import type { CreateClientInput } from "@/features/admin/clients/types";

export function useCreateClient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateClientInput) => createClientApi(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["clients"] });
    },
  });
}