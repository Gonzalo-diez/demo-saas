import { z } from "zod";

export const createSupplierSchema = z.object({
  name: z.string().min(1, "El nombre es obligatorio"),
  tax_id: z.string().optional(),
  email: z
    .string()
    .trim()
    .optional()
    .refine(
      (value) => !value || z.string().email().safeParse(value).success,
      "Email inválido"
    ),
  phone: z.string().optional(),
  address: z.string().optional(),
  is_active: z.boolean(),
});

export const updateSupplierSchema = createSupplierSchema.partial().extend({
  name: z.string().min(1, "El nombre es obligatorio"),
});

export type CreateSupplierFormInput = z.input<typeof createSupplierSchema>;
export type CreateSupplierFormValues = z.output<typeof createSupplierSchema>;

export type UpdateSupplierFormInput = z.input<typeof updateSupplierSchema>;
export type UpdateSupplierFormValues = z.output<typeof updateSupplierSchema>;