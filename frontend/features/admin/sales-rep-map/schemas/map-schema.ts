import { z } from "zod";

export const salesRepMapItemSchema = z.object({
  id: z.number(),
  name: z.string(),
  home_lat: z.number().nullable(),
  home_lng: z.number().nullable(),
  coverage_radius_km: z.number().nullable(),
  home_h3_index: z.string().nullable(),
});

export const salesRepMapResponseSchema = z.object({
  sales_reps: z.array(salesRepMapItemSchema),
});

export type SalesRepMapItem = z.infer<typeof salesRepMapItemSchema>;
export type SalesRepMapResponse = z.infer<typeof salesRepMapResponseSchema>;