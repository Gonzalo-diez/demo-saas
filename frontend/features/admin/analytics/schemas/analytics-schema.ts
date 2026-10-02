import { z } from "zod";

export const analyticsEventTypeSchema = z.enum([
  "product_view",
  "product_click",
  "product_search",
  "sales_rep_view",
  "sales_rep_contact",
  "catalog_open",
]);

export const analyticsCatalogEventSchema = z.object({
  id: z.number(),
  visitor_id: z.string(),
  session_id: z.string(),
  event_type: analyticsEventTypeSchema,
  product_id: z.number().nullable(),
  sales_rep_id: z.number().nullable(),
  zone_h3_index: z.string().nullable(),
  source: z.string().nullable(),
  metadata_json: z.record(z.string(), z.unknown()).nullable(),
  created_at: z.string(),
});

export const catalogEventsListSchema = z.array(analyticsCatalogEventSchema);

export const catalogEventsCountSchema = z.object({ total: z.number() });

export const analyticsDailySchema = z.object({
  id: z.number(),
  date: z.string(),
  total_orders: z.number(),
  total_clients: z.number(),
  total_products_sold: z.number(),
  revenue_generated: z.string(),
  cost_generated: z.string(),
  margin_generated: z.string(),
  average_ticket: z.string(),
  created_at: z.string(),
});

export const analyticsProductDailySchema = z.object({
  id: z.number(),
  date: z.string(),
  product_id: z.number(),
  quantity_sold: z.number(),
  revenue_generated: z.string(),
  cost_generated: z.string(),
  margin_generated: z.string(),
  created_at: z.string(),
});

export const analyticsProductDailyListSchema = z.array(analyticsProductDailySchema);

export const analyticsSalesRepDailySchema = z.object({
  id: z.number(),
  date: z.string(),
  sales_rep_id: z.number(),
  total_orders: z.number(),
  total_clients: z.number(),
  total_products_sold: z.number(),
  revenue_generated: z.string(),
  cost_generated: z.string(),
  margin_generated: z.string(),
  created_at: z.string(),
});

export const analyticsSalesRepDailyListSchema = z.array(analyticsSalesRepDailySchema);

export const productBoughtEntrySchema = z.object({
  product_id: z.number(),
  qty: z.number(),
  amount: z.string(),
  product_name: z.string().nullable().optional(),
  category: z.string().nullable().optional(),
  brand: z.string().nullable().optional(),
});

export const categorySummaryEntrySchema = z.object({
  category: z.string(),
  qty: z.number(),
  amount: z.string(),
  unique_products: z.number(),
});

export const analyticsClientDailySchema = z.object({
  id: z.number(),
  date: z.string(),
  client_id: z.number(),
  total_orders: z.number(),
  revenue_generated: z.string(),
  cost_generated: z.string(),
  margin_generated: z.string(),
  products_bought: z.array(productBoughtEntrySchema),
  unique_products_count: z.number(),
  categories_summary: z.array(categorySummaryEntrySchema).optional().default([]),
  created_at: z.string(),
});

export const analyticsClientDailyListSchema = z.array(analyticsClientDailySchema);

export const analyticsZoneProductDailySchema = z.object({
  id: z.number(),
  date: z.string(),
  h3_index: z.string(),
  product_id: z.number(),
  quantity_sold: z.number(),
  total_orders: z.number(),
  revenue_generated: z.string(),
  cost_generated: z.string(),
  margin_generated: z.string(),
  unique_clients: z.number(),
  created_at: z.string(),
});

export const analyticsZoneProductDailyListSchema = z.array(analyticsZoneProductDailySchema);

export type AnalyticsEventType = z.infer<typeof analyticsEventTypeSchema>;
export type AnalyticsCatalogEvent = z.infer<typeof analyticsCatalogEventSchema>;
export type AnalyticsDaily = z.infer<typeof analyticsDailySchema>;
export type AnalyticsProductDaily = z.infer<typeof analyticsProductDailySchema>;
export type AnalyticsSalesRepDaily = z.infer<typeof analyticsSalesRepDailySchema>;
export type AnalyticsClientDaily = z.infer<typeof analyticsClientDailySchema>;
export type ProductBoughtEntry = z.infer<typeof productBoughtEntrySchema>;
export type CategorySummaryEntry = z.infer<typeof categorySummaryEntrySchema>;
export type AnalyticsZoneProductDaily = z.infer<typeof analyticsZoneProductDailySchema>;