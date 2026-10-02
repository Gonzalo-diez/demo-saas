import { apiFetch } from "@/lib/fetcher";
import type {
  OrderPublic,
  EditOrderPublicInput,
} from "@/features/shop/orders/types";

export const orderEditApi = {
  /**
   * Trae el pedido usando el token que llegó por WhatsApp.
   * GET /api/orders/public/{order_id}/{token}
   */
  get: async (orderId: number, token: string): Promise<OrderPublic> => {
    return apiFetch<OrderPublic>(
      `/api/orders/public/${orderId}/${encodeURIComponent(token)}`,
    );
  },

  /**
   * Guarda la lista de productos actualizada (reemplazo completo).
   * PATCH /api/orders/public/{order_id}/{token}/edit
   */
  edit: async (
    orderId: number,
    token: string,
    data: EditOrderPublicInput,
  ): Promise<OrderPublic> => {
    return apiFetch<OrderPublic>(
      `/api/orders/public/${orderId}/${encodeURIComponent(token)}/edit`,
      {
        method: "PATCH",
        body: JSON.stringify(data),
      },
    );
  },
};