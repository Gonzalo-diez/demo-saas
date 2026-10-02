import { useMutation, useQueryClient } from "@tanstack/react-query";
import { orderShopApi } from "@/features/shop/cart/apis/order-shop-api";
import type { CreateOrderShopInput } from "@/features/shop/cart/types";

export function useCreateOrderShop() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateOrderShopInput) => orderShopApi.create(data),
    onSuccess: () => {
      // Si tienes un historial de órdenes en la shop, lo invalidamos para refrescar
      queryClient.invalidateQueries({ queryKey: ["shop-orders-history"] });
    },
    onError: (error: Error) => {
      throw new Error(error.message || "Error al crear la orden. Intentá nuevamente.");
    },
  });
}