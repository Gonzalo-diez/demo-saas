"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  createTenantApi,
  getTenantsApi,
  setTenantActiveApi,
  updateTenantApi,
} from "@/features/platform/apis/tenants-api";
import type { TenantsQueryParams, UpdateTenantInput } from "@/features/platform/types";

const TENANTS_KEY = ["platform", "tenants"] as const;

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Ocurrió un error";
}

export function useTenants(params: TenantsQueryParams = {}) {
  return useQuery({
    queryKey: [...TENANTS_KEY, params],
    queryFn: () => getTenantsApi(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useCreateTenant() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createTenantApi,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TENANTS_KEY });
      toast.success("Distribuidora creada");
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useUpdateTenant() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ tenantId, data }: { tenantId: number; data: UpdateTenantInput }) =>
      updateTenantApi(tenantId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TENANTS_KEY });
      toast.success("Distribuidora actualizada");
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useSetTenantActive() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ tenantId, active }: { tenantId: number; active: boolean }) =>
      setTenantActiveApi(tenantId, active),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: TENANTS_KEY });
      toast.success(variables.active ? "Distribuidora activada" : "Distribuidora desactivada");
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}
