import { z } from "zod";

export const createProductSchema = z
  .object({
  sku: z.string().min(1, "El SKU es obligatorio").trim(),
  name: z.string().min(1, "El nombre es obligatorio").trim(),
  description: z.string().optional().nullable(),
  // Los dejamos opcionales porque el Backend asigna "Pendiente" o "Sin Clasificar"
  brand: z.string().optional().nullable(),
  category_id: z.number().int().positive().optional().nullable(),
  // Visible en el catálogo de la tienda (la categoría también debe ser pública)
  is_public: z.boolean().default(true),
  unit_cost: z.coerce
    .number()
    .min(0, "El costo debe ser mayor o igual a 0")
    .default(0),
  // Cómo se fija el precio de venta: con un % de remarque sobre el costo (se calcula y
  // se redondea al peso entero) o con un precio fijo.
  pricing_mode: z.enum(["markup", "price"]).default("markup"),
  markup_percent: z.coerce
    .number()
    .min(0, "El remarque debe ser mayor o igual a 0")
    .max(10000, "Remarque demasiado alto")
    .default(0),
  unit_price: z.coerce
    .number()
    .min(0, "El precio debe ser mayor o igual a 0")
    .default(0),
  // Vencimiento del stock inicial (solo al crear; las compras siguientes tienen el suyo).
  expiry_date: z.string().optional().nullable(),
    
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
  })
  .superRefine((data, ctx) => {
    if (data.expiry_date && !(Number(data.stock_current) > 0)) {
      ctx.addIssue({
        code: "custom",
        path: ["expiry_date"],
        message: "Para cargar un vencimiento indicá el stock inicial.",
      });
    }
  });

export type CreateProductFormInput = z.input<typeof createProductSchema>;
export type CreateProductFormValues = z.output<typeof createProductSchema>;