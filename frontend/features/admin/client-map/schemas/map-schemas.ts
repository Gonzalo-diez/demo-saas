import { z } from "zod";

export const clientMapItemSchema = z.object({
  client_id: z.number(),
  client_name: z.string(),
  client_type: z.string(),
  sales_rep_id: z.number().nullable().optional(),
  sales_rep_name: z.string().nullable().optional(),

  branch_id: z.number(),
  branch_name: z.string(),
  branch_address: z.string().nullable().optional(),
  branch_city: z.string().nullable().optional(),
  branch_is_main: z.boolean(),

  lat: z.union([z.number(), z.string()]).transform((value) => Number(value)),
  lng: z.union([z.number(), z.string()]).transform((value) => Number(value)),
  h3_index: z.string().nullable().optional(),
  is_active: z.boolean(),
});

export const clientsMapResponseSchema = z.object({
  clients: z.array(clientMapItemSchema),
});

export type ClientMapItemSchema = z.infer<typeof clientMapItemSchema>;
export type ClientsMapResponseSchema = z.infer<typeof clientsMapResponseSchema>;