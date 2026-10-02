export type OrderStatus = 
  | "pending_confirmation" 
  | "confirmed" 
  | "preparing" 
  | "shipped" 
  | "delivered" 
  | "cancelled";

export type OrderClient = {
  id: number;
  name: string;
};

export type OrderClientBranch = {
  id: number;
  client_id: number;
  name: string;
  address: string | null;
  city: string | null;
};

export type OrderSalesRep = {
  id: number;
  name: string;
  email: string;
};

export type OrderItemAdmin = {
  id: number;
  product_id: number;
  product_name_snapshot: string;
  product_brand_snapshot: string | null;
  product_sku_snapshot: string | null;
  product_image_url: string  | null;
  quantity: number;
  unit_cost: number;
  unit_price: number;
  subtotal_cost: number;
  subtotal: number;
  margin_amount: number;
};

export type AdminOrder = {
  id: number;
  status: OrderStatus;

  // Relaciones Online
  customer_name: string;
  customer_email: string;
  customer_phone: string;

  // Verificación de identidad / datos fiscales (Ley 26.687 + facturación)
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
  delivery_address: string | null;
  delivery_city: string | null;
  delivery_reference: string | null;
  preferred_delivery_date: string;
  scheduled_delivery_date: string;
  sales_type: "ONLINE" | "B2B";
  // Relaciones B2B estrictas
  client_id: number;
  client_branch_id: number | null;
  sales_rep_id: number;
  
  client?: OrderClient | null;
  client_branch?: OrderClientBranch | null;
  sales_rep?: OrderSalesRep | null;

  total_cost: number;
  total_amount: number;
  margin_amount: number;
  currency: string;

  document_type: "sales_invoice" | "sales_quote";
  // Nombre histórico: significa "documento de venta generado" (remito o presupuesto).
  invoice_generated: boolean;

  items: OrderItemAdmin[];
  created_at: string;
};

export type CreateOrderB2BInput = {
  client_id: number;
  client_branch_id: number | null;
  document_type: "sales_invoice" | "sales_quote";
  items: { product_id: number; quantity: number }[];
};

export type PaginatedAdminOrdersResponse = {
  items: AdminOrder[];
  total: number;
  page: number;
  page_size: number;
};

export type AdminOrderQueryParams = {
  page?: number;
  page_size?: number;
  status?: OrderStatus;
  client_id?: number;
};

export type UpdateOrderStatusInput = {
  status: OrderStatus; 
};

export type OrderScheduleDelivery = {
  scheduled_delivery_date: string;
}

export type UpdateOrderB2BInput = {
  client_branch_id?: number | null;
  status?: OrderStatus;
  document_type?: "sales_invoice" | "sales_quote";
};

export type EditOrderB2BInput = {
  items: { product_id: number; quantity: number }[];
  client_branch_id?: number | null;
  delivery_reference?: string | null;
};

export type EditOrderShopInput = {
  items: { product_id: number; quantity: number }[];
  customer_name?: string | null;
  customer_phone?: string | null;
  customer_email?: string | null;
  delivery_type?: "delivery" | "pickup" | null;
  delivery_address?: string | null;
  delivery_city?: string | null;
  delivery_reference?: string | null;
  preferred_delivery_date?: string | null;
};