export type AnalyticsEventType =
  | "product_view"
  | "product_click"
  | "product_search"
  | "sales_rep_view"
  | "sales_rep_contact"
  | "catalog_open";

export interface AnalyticsCatalogEvent {
  id: number;
  visitor_id: string;
  session_id: string;
  event_type: AnalyticsEventType;
  product_id: number | null;
  sales_rep_id: number | null;
  zone_h3_index: string | null;
  source: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
}

export interface CatalogEventsQueryParams {
  start_date?: string;
  end_date?: string;
  event_type?: AnalyticsEventType;
  product_id?: number;
  sales_rep_id?: number;
  visitor_id?: string;
  session_id?: string;
  limit?: number;
  offset?: number;
}

export interface AnalyticsDailyRead {
  id: number;
  date: string;
  total_orders: number;
  total_clients: number;
  total_products_sold: number;
  revenue_generated: string;
  cost_generated: string;
  margin_generated: string;
  average_ticket: string;
  created_at: string;
}

export interface AnalyticsProductDailyRead {
  id: number;
  date: string;
  product_id: number;
  quantity_sold: number;
  revenue_generated: string;
  cost_generated: string;
  margin_generated: string;
  created_at: string;
}

export interface AnalyticsSalesRepDailyRead {
  id: number;
  date: string;
  sales_rep_id: number;
  total_orders: number;
  total_clients: number;
  total_products_sold: number;
  revenue_generated: string;
  cost_generated: string;
  margin_generated: string;
  created_at: string;
}

export interface ProductBoughtEntry {
  product_id: number;
  qty: number;
  product_name: string;
  category: string;
  brand: string;
  amount: string;
}

export interface CategoriesSummary {
  category: string;
  qty: number;
  amount: string;
  unique_products: number;
}

export interface AnalyticsClientDailyRead {
  id: number;
  date: string;
  client_id: number;
  total_orders: number;
  revenue_generated: string;
  cost_generated: string;
  margin_generated: string;
  products_bought: ProductBoughtEntry[];
  unique_products_count: number;
  created_at: string;
}

export interface AnalyticsZoneProductDailyRead {
  id: number;
  date: string;
  h3_index: string;
  product_id: number;
  quantity_sold: number;
  total_orders: number;
  revenue_generated: string;
  cost_generated: string;
  margin_generated: string;
  unique_clients: number;
  created_at: string;
}

export interface DailyQueryParams {
  target_date: string; // "YYYY-MM-DD"
}

export interface ClientHistoryParams {
  client_id: number;
  start_date: string;
  end_date: string;
  limit?: number;
}