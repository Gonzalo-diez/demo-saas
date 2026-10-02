import { z } from "zod";

const emptyStringToNullNumber = z.preprocess((value) => {
  if (value === "" || value === undefined || value === null) return null;
  return value;
}, z.coerce.number().nullable());

export const clientBranchSchema = z
  .object({
    name: z
      .string()
      .min(1, "El nombre de la sucursal es obligatorio")
      .max(255, "Máximo 255 caracteres"),
    address: z
      .string()
      .max(255, "Máximo 255 caracteres")
      .optional()
      .or(z.literal("")),
    city: z
      .string()
      .max(100, "Máximo 100 caracteres")
      .optional()
      .or(z.literal("")),
    lat: emptyStringToNullNumber.refine(
      (value) => value == null || (value >= -90 && value <= 90),
      "La latitud debe estar entre -90 y 90"
    ),
    lng: emptyStringToNullNumber.refine(
      (value) => value == null || (value >= -180 && value <= 180),
      "La longitud debe estar entre -180 y 180"
    ),
    h3_index: z
      .string()
      .max(32, "Máximo 32 caracteres")
      .optional()
      .or(z.literal("")),
    contact_name: z
      .string()
      .max(255, "Máximo 255 caracteres")
      .optional()
      .or(z.literal("")),
    contact_phone: z
      .string()
      .max(50, "Máximo 50 caracteres")
      .optional()
      .or(z.literal("")),
    reference: z
      .string()
      .max(255, "Máximo 255 caracteres")
      .optional()
      .or(z.literal("")),
    is_main: z.boolean(),
    is_active: z.boolean().default(true),
  })
  .refine(
    (branch) =>
      (branch.lat == null && branch.lng == null) ||
      (branch.lat != null && branch.lng != null),
    {
      message: "Latitud y longitud deben completarse juntas",
      path: ["lat"],
    }
  );

export const createClientSchema = z
  .object({
    name: z
      .string()
      .min(1, "El nombre del cliente es obligatorio")
      .max(255, "Máximo 255 caracteres"),
    email: z
      .string()
      .email("Email inválido")
      .max(255, "Máximo 255 caracteres")
      .optional()
      .or(z.literal("")),
    phone: z
      .string()
      .max(50, "Máximo 50 caracteres")
      .optional()
      .or(z.literal("")),
    tax_id: z
      .string()
      .max(50, "Máximo 50 caracteres")
      .optional()
      .or(z.literal("")),
    client_type: z
      .string()
      .min(1, "El tipo de cliente es obligatorio")
      .max(50, "Máximo 50 caracteres"),
    password: z
      .string()
      .min(6, "La contraseña debe tener al menos 6 caracteres")
      .max(255, "Máximo 255 caracteres"),
    is_active: z.boolean().default(true),
    branches: z
      .array(clientBranchSchema)
      .min(1, "Debes agregar al menos una sucursal"),
  })
  .refine(
    (data) => data.branches.filter((branch) => branch.is_main).length === 1,
    {
      message: "Debe existir exactamente una sucursal principal",
      path: ["branches"],
    }
  );

export const updateClientSchema = z.object({
  name: z
    .string()
    .min(1, "El nombre del cliente es obligatorio")
    .max(255, "Máximo 255 caracteres"),
  email: z
    .email("Email inválido")
    .max(255, "Máximo 255 caracteres")
    .optional()
    .or(z.literal("")),
  phone: z
    .string()
    .max(50, "Máximo 50 caracteres")
    .optional()
    .or(z.literal("")),
  tax_id: z
    .string()
    .max(50, "Máximo 50 caracteres")
    .optional()
    .or(z.literal("")),
  password: z
    .string()
    .min(6, "La contraseña debe tener al menos 6 caracteres")
    .max(255, "Máximo 255 caracteres")
    .optional()
    .or(z.literal("")),
  is_active: z.boolean().default(true),
});

export type ClientBranchFormInput = z.input<typeof clientBranchSchema>;
export type ClientBranchFormValues = z.output<typeof clientBranchSchema>;

export type CreateClientFormInput = z.input<typeof createClientSchema>;
export type CreateClientFormValues = z.output<typeof createClientSchema>;

export type UpdateClientFormInput = z.input<typeof updateClientSchema>;
export type UpdateClientFormValues = z.output<typeof updateClientSchema>;