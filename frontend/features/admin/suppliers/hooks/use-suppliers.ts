"use client";

import { useQuery } from "@tanstack/react-query";
import { getSuppliersApi } from "@/features/admin/suppliers/apis/suppliers-api";
import type { SupplierListParams } from "@/features/admin/suppliers/types";

export function useSuppliers(params: SupplierListParams = {}) {
  return useQuery({
    queryKey: ["suppliers", params],
    queryFn: () => getSuppliersApi(params),
  });
}