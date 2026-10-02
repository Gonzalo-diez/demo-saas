export type OrderItemShop = {
  id: number;
  product_id: number;
  product_name_snapshot: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
};

export type ClientBranch = {
  id: number;
  client_id: number;
  name: string;
  address: string | null;
  city: string | null;
  is_main: boolean;
};

export type ShopOrder = {
  id: number;
  status: string;
  customer_name: string;
  customer_phone: string;
  customer_email: string;

  customer_dni: string | null;
  age_confirmed: boolean;
  customer_tax_id: string | null;
  customer_person_type: "individual" | "empresa" | null;
  customer_iva_condition:
    | "consumidor_final"
    | "responsable_inscripto"
    | "monotributista"
    | "exento"
    | null;

  delivery_type: "delivery" | "pickup";
  delivery_address: string;
  delivery_city: string;
  delivery_reference: string | null;
  preferred_delivery_date: string | null;

  client_branch_id: number | null;
  client_branch: ClientBranch | null;

  total_amount: number;
  currency: string;

  items: OrderItemShop[];
  created_at: string;
};

export type CreateOrderShopInput = {
  customer_name: string;
  customer_phone: string;
  customer_email: string;
  customer_dni?: string;
  age_confirmed?: boolean;
  customer_tax_id?: string;
  customer_person_type?: "individual" | "empresa";
  customer_iva_condition?:
    | "consumidor_final"
    | "responsable_inscripto"
    | "monotributista"
    | "exento";

  delivery_type: "delivery" | "pickup";
  delivery_address: string;
  delivery_city: string;
  delivery_reference?: string;
  preferred_delivery_date: string;

  // Sucursal del cliente logueado a la que corresponde el pedido
  // (opcional: no todos los clientes tienen sucursales cargadas).
  client_branch_id?: number | null;
  document_type: "sales_invoice" | "sales_quote";
};

export type PaginatedShopOrdersResponse = {
  items: ShopOrder[];
  total_amount: number;
  page: number;
  page_size: number;
};

export type UpdateOrderShopInput = {
  customer_phone?: string;
  delivery_address?: string;
  delivery_city?: string;
};