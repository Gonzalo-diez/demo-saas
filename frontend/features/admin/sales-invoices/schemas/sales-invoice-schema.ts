import { z } from "zod";

export const createSalesInvoiceItemSchema = z.object({
  product_id: z.coerce.number().int().positive("Seleccioná un producto"),
  product_name: z.string().trim().min(1, "El nombre del producto es obligatorio"),
  quantity: z.coerce.number().int().positive("La cantidad debe ser mayor a 0"),
});

export const createSalesInvoiceSchema = z.object({
  sales_type: z.enum(["B2B", "ONLINE"], {
    message: "Seleccioná el tipo de venta",
  }),
  order_id: z.coerce
    .number()
    .int()
    .positive("La orden debe ser válida")
    .nullable(),
  client_id: z.coerce.number().int().positive("Seleccioná un cliente"),
  client_branch_id: z.coerce
    .number()
    .int()
    .positive("Seleccioná una sucursal válida")
    .nullable(),
  invoice_number: z
    .string()
    .trim()
    .min(1, "El número de remito es obligatorio")
    .max(100, "Máximo 100 caracteres"),
  invoice_date: z.string().min(1, "La fecha es obligatoria"),
  notes: z
    .string()
    .trim()
    .max(1000, "Máximo 1000 caracteres")
    .optional()
    .or(z.literal("")),
  items: z.array(createSalesInvoiceItemSchema).min(1, "Agregá al menos un ítem"),
});

export type CreateSalesInvoiceFormInput = z.input<typeof createSalesInvoiceSchema>;
export type CreateSalesInvoiceFormValues = z.output<typeof createSalesInvoiceSchema>;