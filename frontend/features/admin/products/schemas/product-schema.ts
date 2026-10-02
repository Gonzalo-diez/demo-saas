import { z } from "zod";

export const createProductSchema = z.object({
  sku: z.string().min(1, "El SKU es obligatorio").trim(),
  name: z.string().min(1, "El nombre es obligatorio").trim(),
  description: z.string().optional().nullable(),
  // Los dejamos opcionales porque el Backend asigna "Pendiente" o "Sin Clasificar"
  brand: z.string().optional().nullable(),
  category: z.string().optional().nullable(),
  unit_cost: z.coerce
    .number()
    .min(0, "El costo debe ser mayor o igual a 0")
    .default(0),
  unit_price: z.coerce
    .number()
    .min(0, "El precio debe ser mayor o igual a 0")
    .default(0),
    
  stock_current: z.coerce
    .number()
    .int("El stock debe ser un número entero")
    .min(0, "Mínimo 0")
    .default(0),
  stock_min: z.coerce
    .number()
    .int("El stock debe ser un número entero")
    .min(0, "Mínimo 0")
    .default(0),
  image_url: z.url("Debe ser una URL válida").optional().nullable(),
});

export type CreateProductFormInput = z.input<typeof createProductSchema>;
export type CreateProductFormValues = z.output<typeof createProductSchema>;