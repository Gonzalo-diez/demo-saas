import * as z from "zod";

function today() {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  return d;
}

function maxDate() {
  const d = today();
  d.setDate(d.getDate() + 30);
  return d;
}

const baseOrderShopSchema = z.object({
  customer_name: z.string().min(3, "El nombre es obligatorio"),
  customer_phone: z.string().min(8, "El teléfono es obligatorio"),
  customer_email: z.email("Correo electrónico inválido"),

  delivery_type: z.enum(["delivery", "pickup"]),

  delivery_address: z.string(),
  delivery_city: z.string(),
  delivery_reference: z.string().optional(),

  client_branch_id: z.number().int().positive().nullable().optional(),

  preferred_delivery_date: z
    .string()
    .min(1, "La fecha de entrega es obligatoria")
    .refine(
      (val) => {
        const selected = new Date(val);
        selected.setHours(0, 0, 0, 0);
        return selected >= today();
      },
      { error: "La fecha no puede ser en el pasado" }
    )
    .refine(
      (val) => {
        const selected = new Date(val);
        selected.setHours(0, 0, 0, 0);
        return selected <= maxDate();
      },
      { error: "La fecha no puede ser mayor a 30 días desde hoy" }
    ),

  customer_dni: z.string().optional(),
  age_confirmed: z.boolean().optional(),

  customer_tax_id: z.string().optional(),
  customer_person_type: z.enum(["individual", "empresa"]).optional(),
  customer_iva_condition: z
    .enum([
      "consumidor_final",
      "responsable_inscripto",
      "monotributista",
      "exento",
    ])
    .optional(),

  document_type: z.enum(["sales_invoice", "sales_quote"], {
    error: "Debés seleccionar el tipo de documento",
  }),
});

/**
 * `hasRegulatedItems` viene del carrito (calculado en el componente,
 * fuera del schema, porque el schema no tiene acceso a los productos).
 * Cuando es true, exige DNI válido + el checkbox de mayoría de edad.
 */
export function createOrderShopSchema(hasRegulatedItems: boolean) {
  return baseOrderShopSchema
    .refine(
      (data) =>
        data.delivery_type === "pickup" ||
        (data.delivery_address && data.delivery_city),
      {
        error: "Dirección y ciudad obligatorias para envío",
        path: ["delivery_address"],
      }
    )
    .superRefine((data, ctx) => {
      if (!hasRegulatedItems) return;

      if (!data.customer_dni || data.customer_dni.replace(/\D/g, "").length < 7) {
        ctx.addIssue({
          code: "custom",
          path: ["customer_dni"],
          error:
            "Tu pedido incluye productos de tabaco: el DNI es obligatorio.",
        });
      }

      if (!data.age_confirmed) {
        ctx.addIssue({
          code: "custom",
          path: ["age_confirmed"],
          error: "Tenés que confirmar que sos mayor de 18 años.",
        });
      }
    });
}

export type CreateOrderShopFormValues = z.infer<typeof baseOrderShopSchema>;