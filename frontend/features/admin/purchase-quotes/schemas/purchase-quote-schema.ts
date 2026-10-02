import { z } from "zod";

export const createPurchaseQuoteItemSchema = z.object({
  product_id: z.coerce.number().int().positive().nullable().optional(),
  product_name: z.string().trim().min(1, "El nombre del producto es obligatorio"),
  quantity: z.coerce.number().int().positive("La cantidad debe ser mayor a 0"),
  unit_cost: z.coerce.number().min(0, "El costo no puede ser negativo"),
  discount_amount: z.coerce.number().min(0).optional(),
});

export const createPurchaseQuoteSchema = z.object({
  supplier_id: z.coerce.number().int().positive("Seleccioná un proveedor").nullable(),
  quote_number: z
    .string()
    .trim()
    .min(1, "El número de presupuesto es obligatorio")
    .max(100, "Máximo 100 caracteres"),
  quote_date: z.string().min(1, "La fecha es obligatoria"),
  valid_until: z.string().optional().or(z.literal("")),
  notes: z
    .string()
    .trim()
    .max(1000, "Máximo 1000 caracteres")
    .optional()
    .or(z.literal("")),
  items: z.array(createPurchaseQuoteItemSchema).min(1, "Agregá al menos un ítem"),
});

export type CreatePurchaseQuoteFormInput = z.input<typeof createPurchaseQuoteSchema>;
export type CreatePurchaseQuoteFormValues = z.output<typeof createPurchaseQuoteSchema>;
