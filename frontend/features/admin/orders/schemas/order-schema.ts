import { z } from "zod";

export const createOrderItemAdminSchema = z.object({
  product_id: z.number().int().positive("Producto inválido"),
  quantity: z
    .number()
    .int("La cantidad debe ser un número entero")
    .positive("La cantidad debe ser mayor a 0"),
});

export const createOrderB2BSchema = z.object({
  // Obligatorio para B2B
  client_id: z
    .number({ error: "El cliente es obligatorio" })
    .int()
    .positive("Cliente inválido"),
  
  client_branch_id: z
    .number()
    .int()
    .positive("Sucursal inválida")
    .nullable()
    .optional(),
  
  document_type:
    z.enum(["sales_invoice", "sales_quote"], {
      error: "Debes seleccionar el tipo de documento."
    }),
  
  items: z
    .array(createOrderItemAdminSchema)
    .min(1, "Agregá al menos un producto")
    .refine((items) => {
      const ids = items.map((item) => item.product_id);
      return new Set(ids).size === ids.length;
    }, "No podés repetir productos en la misma orden"),
});

export const updateOrderB2BSchema = z.object({
  client_branch_id: z.number().int().positive().nullable().optional(),
});

export const updateOrderStatusSchema = z.object({
  status: z.enum([
    "pending_confirmation",
    "confirmed",
    "preparing",
    "shipped",
    "delivered",
    "cancelled",
  ]),
});

export const editOrderB2BSchema = z.object({
  client_branch_id: z.number().int().positive().nullable().optional(),
  delivery_reference: z.string().nullable().optional(),
  document_type: z.enum(["sales_invoice", "sales_quote"]).optional(),
  items: z
    .array(createOrderItemAdminSchema)
    .min(1, "Agregá al menos un producto")
    .refine((items) => {
      const ids = items.map((i) => i.product_id);
      return new Set(ids).size === ids.length;
    }, "No podés repetir productos"),
});

export const editOrderShopSchema = z.object({
  customer_name: z.string().min(1, "El nombre es obligatorio").nullable().optional(),
  customer_phone: z.string().min(5, "Teléfono inválido").nullable().optional(),
  customer_email: z.email("Email inválido").nullable().optional(),
  delivery_type: z.enum(["delivery", "pickup"]).nullable().optional(),
  delivery_address: z.string().nullable().optional(),
  delivery_city: z.string().nullable().optional(),
  delivery_reference: z.string().nullable().optional(),
  preferred_delivery_date: z.string().nullable().optional(),
  items: z
    .array(createOrderItemAdminSchema)
    .min(1, "Agregá al menos un producto")
    .refine((items) => {
      const ids = items.map((i) => i.product_id);
      return new Set(ids).size === ids.length;
    }, "No podés repetir productos en la misma orden"),
});

export const scheduleDeliveryDateSchema = z.object({
  scheduled_delivery_date: z.string(),
});

export type CreateOrderB2BFormValues = z.output<typeof createOrderB2BSchema>;
export type UpdateOrderB2BFormValues = z.infer<typeof updateOrderB2BSchema>;
export type UpdateOrderStatusFormValues = z.infer<typeof updateOrderStatusSchema>;
export type EditOrderB2BFormValues = z.infer<typeof editOrderB2BSchema>;
export type EditOrderShopFormValues = z.infer<typeof editOrderShopSchema>;
export type ScheduleDeliveryDateFormValues = z.infer<typeof scheduleDeliveryDateSchema>;