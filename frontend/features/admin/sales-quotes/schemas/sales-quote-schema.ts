import { z } from "zod";

export const createSalesQuoteItemSchema = z.object({
  product_id: z.coerce.number().int().positive().nullable().optional(),
  product_name: z.string().trim().min(1, "El nombre del producto es obligatorio"),
  quantity: z.coerce.number().int().positive("La cantidad debe ser mayor a 0"),
  unit_price: z.coerce.number().min(0, "El precio no puede ser negativo"),
  discount_amount: z.coerce.number().min(0).optional(),
});

export const createSalesQuoteSchema = z.object({
  client_id: z.coerce.number().int().positive("Seleccioná un cliente").nullable(),
  client_branch_id: z.coerce.number().int().positive().nullable().optional(),
  quote_number: z
    .string()
    .trim()
    .min(1, "El número de presupuesto es obligatorio")
    .max(100, "Máximo 100 caracteres"),
  quote_date: z.string().min(1, "La fecha es obligatoria"),
  valid_until: z.string().optional().or(z.literal("")),
  payment_method: z.string().trim().max(50).optional().or(z.literal("")),
  notes: z
    .string()
    .trim()
    .max(1000, "Máximo 1000 caracteres")
    .optional()
    .or(z.literal("")),
  items: z.array(createSalesQuoteItemSchema).min(1, "Agregá al menos un ítem"),
});

export type CreateSalesQuoteFormInput = z.input<typeof createSalesQuoteSchema>;
export type CreateSalesQuoteFormValues = z.output<typeof createSalesQuoteSchema>;
