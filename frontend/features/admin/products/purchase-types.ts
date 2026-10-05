// Espejo de app/schemas/product_purchase_schema.py

export type PurchaseSource =
  | "initial_stock"
  | "manual"
  | "purchase_invoice"
  | "import";

export type ProductPurchase = {
  id: number;
  product_id: number;
  purchase_date: string; // YYYY-MM-DD
  quantity: number;
  unit_cost: number;
  markup_percent: number | null;
  sale_price: number | null;
  expiry_date: string | null; // YYYY-MM-DD
  source: PurchaseSource;
  reference_id: number | null;
  notes: string | null;
  created_by: number | null;
  created_by_name: string | null;
  created_at: string;
};

export type ProductPurchaseSummary = {
  purchases_count: number;
  total_quantity: number;
  /** Costo promedio ponderado de todas las compras registradas. */
  average_cost: number | null;
  last_cost: number | null;
  min_cost: number | null;
  max_cost: number | null;
  /** Vencimiento más cercano (de hoy en adelante). Es una referencia: no descuenta lo vendido. */
  next_expiry_date: string | null;
};

export type ProductPurchaseListResponse = {
  items: ProductPurchase[];
  total: number;
  page: number;
  page_size: number;
  summary: ProductPurchaseSummary;
};

export type CreateProductPurchaseInput = {
  quantity: number;
  unit_cost: number;
  markup_percent?: number;
  sale_price?: number;
  expiry_date?: string | null;
  purchase_date?: string | null;
  notes?: string | null;
  update_product_price?: boolean;
};

export const PURCHASE_SOURCE_LABELS: Record<PurchaseSource, string> = {
  initial_stock: "Stock inicial",
  manual: "Compra manual",
  purchase_invoice: "Remito de compra",
  import: "Importación",
};
