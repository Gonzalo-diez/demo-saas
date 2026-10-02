import { z } from "zod";

export const editOrderShopSchema = z.object({
  customer_name: z
    .string()
    .min(1, "El nombre es obligatorio")
    .nullable()
    .optional(),
  customer_phone: z.string().min(5, "Teléfono inválido").nullable().optional(),
  customer_email: z.email("Email inválido").nullable().optional(),
  delivery_type: z.enum(["delivery", "pickup"]).nullable().optional(),
  delivery_city: z.string().nullable().optional(),
  delivery_address: z.string().nullable().optional(),
  delivery_reference: z.string().nullable().optional(),
  preferred_delivery_date: z.string().nullable().optional(),
  items: z
    .array(z.object({
      product_id: z.number().int().positive("Producto inválido"),
      quantity: z.number().int().positive("Cantidad inválida"),
    }))
    .min(1, "Agregá al menos un producto")
    .refine((items) => {
        const ids = items.map((i) => i.product_id);
        return new Set(ids).size === ids.length;
    }, "No podés repetir productos en la misma orden"),
});

export type EditShopOrderFormValues = z.infer<typeof editOrderShopSchema>;