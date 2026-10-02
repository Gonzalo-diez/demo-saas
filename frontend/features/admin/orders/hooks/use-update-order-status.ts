"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateOrderStatusApi } from "@/features/admin/orders/apis/orders-api";
import type { OrderStatus } from "@/features/admin/orders/types";
import { toast } from "sonner";

type UpdateOrderStatusPayload = {
  orderId: number;
  status: OrderStatus;
};

export function useUpdateOrderStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    // Recibimos orderId y status como argumentos del hook
    mutationFn: ({ orderId, status }: { orderId: number; status: OrderStatus }) =>
      updateOrderStatusApi(orderId, { status }), // Pasamos un objeto que cumple con UpdateOrderStatusInput
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["admin", "orders"], exact: false });
      queryClient.invalidateQueries({ queryKey: ["admin", "orders", variables.orderId] });
      queryClient.invalidateQueries({ queryKey: ["products"] });
      toast.success("Estado actualizado correctamente");
    },
  });
}