"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  createPlatformAdminApi,
  deletePlatformAdminApi,
  getPlatformAdminsApi,
  updatePlatformAdminApi,
} from "@/features/platform/apis/platform-admins-api";
import type { UpdatePlatformAdminInput } from "@/features/platform/types";

const ADMINS_KEY = ["platform", "admins"] as const;

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Ocurrió un error";
}

export function usePlatformAdmins() {
  return useQuery({
    queryKey: ADMINS_KEY,
    queryFn: getPlatformAdminsApi,
  });
}

export function useCreatePlatformAdmin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createPlatformAdminApi,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ADMINS_KEY });
      toast.success("Administrador creado");
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useUpdatePlatformAdmin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ adminId, data }: { adminId: number; data: UpdatePlatformAdminInput }) =>
      updatePlatformAdminApi(adminId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ADMINS_KEY });
      toast.success("Administrador actualizado");
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useDeletePlatformAdmin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (adminId: number) => deletePlatformAdminApi(adminId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ADMINS_KEY });
      toast.success("Administrador eliminado");
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}
