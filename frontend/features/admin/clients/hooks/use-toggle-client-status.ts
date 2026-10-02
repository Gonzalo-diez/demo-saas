"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  activateClientApi,
  deactivateClientApi,
} from "@/features/admin/clients/apis/clients-api";

type ToggleStatusClientPayload = {
  clientId: number;
  clientName?: string;
  isActive: boolean;
};

export function useToggleClientStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      clientId,
      isActive,
    }: ToggleStatusClientPayload) => {
      if (isActive) {
        return deactivateClientApi(clientId);
      }

      return activateClientApi(clientId);
    },

    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["clients"] });
      queryClient.invalidateQueries({ queryKey: ["clients-map"] });

      toast.success(
        variables.isActive
          ? `Cliente desactivado${variables.clientName ? `: ${variables.clientName}` : ""}`
          : `Cliente activado${variables.clientName ? `: ${variables.clientName}` : ""}`
      );
    },

    onError: (error, variables) => {
      toast.error(
        error instanceof Error
          ? error.message
          : variables.isActive
            ? "No se pudo desactivar el cliente"
            : "No se pudo activar el cliente"
      );
    },
  });
}