export type OrderPublicItem = {
  id: number;
  product_id: number;
  product_name_snapshot: string;
  product_brand_snapshot: string | null;
  product_sku_snapshot: string | null;
  product_image_url_snapshot: string | null;
  quantity: number;
  unit_price: number;
  subtotal: number;
};

export type OrderPublic = {
  id: number;
  status:
    | "pending_confirmation"
    | "confirmed"
    | "preparing"
    | "shipped"
    | "delivered"
    | "cancelled";

  customer_name: string | null;
  customer_phone: string | null;
  customer_email: string | null;

  delivery_type: "delivery" | "pickup" | null;
  delivery_address: string | null;
  delivery_city: string | null;
  delivery_reference: string | null;

  preferred_delivery_date: string | null;

  total_amount: number;
  currency: string;

  items: OrderPublicItem[];

  created_at: string;
};

export type EditOrderPublicItemInput = {
  product_id: number;
  quantity: number;
};

export type EditOrderPublicInput = {
  items: EditOrderPublicItemInput[];
};

// El pedido solo se puede editar en estos estados (ver order_service.py)
export const EDITABLE_ORDER_STATUSES = new Set([
  "pending_confirmation",
  "confirmed",
  "preparing",
]);