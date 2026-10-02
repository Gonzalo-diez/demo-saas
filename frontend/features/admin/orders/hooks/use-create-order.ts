"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createOrderB2BApi } from "@/features/admin/orders/apis/orders-api";
import type { CreateOrderB2BInput } from "@/features/admin/orders/types";
import { toast } from "sonner";

export function useCreateOrderB2B() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateOrderB2BInput) => createOrderB2BApi(data),
    onSuccess: () => {
      // Invalidamos la lista para ver la nueva orden arriba
      queryClient.invalidateQueries({ queryKey: ["admin", "orders"] });
      // El backend descuenta stock, así que debemos refrescar productos
      queryClient.invalidateQueries({ queryKey: ["products"] });
      toast.success("Orden B2B creada con éxito");
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Error al crear la orden",
      );
    }
  });
}