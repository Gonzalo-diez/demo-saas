"use client";

import { useQuery } from "@tanstack/react-query";
import { getOrdersApi } from "@/features/admin/orders/apis/orders-api";
import type { AdminOrderQueryParams } from "@/features/admin/orders/types";

export function useAdminOrders(params: AdminOrderQueryParams) {
  return useQuery({
    // La clave incluye los params para que al cambiar de página o filtro se dispare el fetch
    queryKey: ["admin", "orders", params],
    queryFn: () => getOrdersApi(params),
    placeholderData: (previousData) => previousData, // Evita el "parpadeo" blanco al cambiar de página
    staleTime: 1000 * 60 * 5, // 5 minutos de caché para datos de admin
  });
}