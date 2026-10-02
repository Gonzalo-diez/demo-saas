import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { orderEditApi } from "@/features/shop/orders/apis/order-edit-api";
import type { EditOrderPublicInput } from "@/features/shop/orders/types";

export function useOrderPublic(orderId: number, token: string) {
  return useQuery({
    queryKey: ["order-public", orderId, token],
    queryFn: () => orderEditApi.get(orderId, token),
    enabled: Boolean(orderId) && Boolean(token),
  });
}

export function useEditOrderPublic(orderId: number, token: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: EditOrderPublicInput) =>
      orderEditApi.edit(orderId, token, data),
    onSuccess: (updatedOrder) => {
      queryClient.setQueryData(["order-public", orderId, token], updatedOrder);
    },
  });
}