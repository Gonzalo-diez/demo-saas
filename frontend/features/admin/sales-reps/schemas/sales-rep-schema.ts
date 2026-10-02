import { z } from "zod";

export const createSalesRepSchema = z.object({
  name: z.string().min(1, "El nombre es obligatorio"),
  email: z.email("Email inválido"),
  phone: z.string().optional(),
  home_lat: z.union([z.number(), z.string()]).transform((value) => Number(value)),
  home_lng: z.union([z.number(), z.string()]).transform((value) => Number(value)),
  coverage_radius_km: z.union([z.number(), z.string()]).transform((value) => Number(value)),
  home_h3_index: z.string().nullable().optional().or(z.literal("")),
  password: z
    .string()
    .min(6, "La contraseña debe tener al menos 6 caracteres"),
  is_active: z.boolean(),
  is_superuser: z.boolean(),
});

export const updateSalesRepSchema = createSalesRepSchema.extend({
  password: z
    .string()
    .min(6, "La contraseña debe tener al menos 6 caracteres")
    .optional()
    .or(z.literal("")),
});

export type CreateSalesRepFormInput = z.input<typeof createSalesRepSchema>;
export type CreateSalesRepFormValues = z.output<typeof createSalesRepSchema>;

export type UpdateSalesRepFormInput = z.input<typeof updateSalesRepSchema>;
export type UpdateSalesRepFormValues = z.output<typeof updateSalesRepSchema>;