import { z } from "zod";

export const createPurchaseInvoiceItemSchema = z.object({
  product_id: z.coerce.number().int().positive("Seleccioná un producto"),
  quantity: z.coerce.number().int().positive("La cantidad debe ser mayor a 0"),
  unit_cost: z.coerce.number().positive("El costo debe ser mayor a 0"),
});

export const createPurchaseInvoiceSchema = z.object({
  supplier_id: z.coerce.number().int().positive("Seleccioná un proveedor"),
  invoice_number: z
    .string()
    .trim()
    .min(1, "El número de remito es obligatorio")
    .max(100, "Máximo 100 caracteres"),
  invoice_date: z.string().min(1, "La fecha es obligatoria"),
  notes: z.string().trim().max(1000, "Máximo 1000 caracteres").optional().or(z.literal("")),
  items: z.array(createPurchaseInvoiceItemSchema).min(1, "Agregá al menos un ítem"),
});

export type CreatePurchaseInvoiceFormInput = z.input<
  typeof createPurchaseInvoiceSchema
>;
export type CreatePurchaseInvoiceFormValues = z.output<
  typeof createPurchaseInvoiceSchema
>;