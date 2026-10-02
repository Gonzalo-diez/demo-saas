"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { scheduleDeliveryApi } from "@/features/admin/orders/apis/orders-api";
import { toast } from "sonner";

export function useScheduleDeliveryDate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ orderId, scheduled_delivery_date }: { orderId: number; scheduled_delivery_date: string }) =>
      scheduleDeliveryApi(orderId, { scheduled_delivery_date }),
    onSuccess: (_, { orderId }) => {
      queryClient.invalidateQueries({ queryKey: ["admin", "orders"], exact: false });
      queryClient.invalidateQueries({ queryKey: ["admin", "orders", orderId] });
      toast.success("Fecha de entrega programada correctamente");
    },
    onError: (error) => {
      toast.error(
        error instanceof Error
          ? error.message
          : "Error al programar la fecha de entrega",
      );
    },
  });
}