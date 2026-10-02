import { apiFetch } from "@/lib/fetcher";
import type { CreateOrderShopInput, ShopOrder } from "@/features/shop/cart/types";

export const orderShopApi = {
  /**
   * Crea una nueva orden desde la tienda pública.
   * Envía un POST a `${API_URL}/orders`.
   */
  create: async (data: CreateOrderShopInput): Promise<ShopOrder> => {
    return apiFetch<ShopOrder>("/api/orders", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
};