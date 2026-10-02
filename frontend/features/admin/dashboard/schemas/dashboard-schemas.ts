import { z } from "zod";

export const dashboardSummarySchema = z.object({
  products_total: z.number(),
  clients_total: z.number(),
  orders_total: z.number(),
  sales_reps_total: z.number(),
});

export type DashboardSummary = z.infer<typeof dashboardSummarySchema>;