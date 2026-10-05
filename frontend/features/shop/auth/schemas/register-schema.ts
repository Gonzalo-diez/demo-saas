import { z } from "zod";

export const clientRegisterSchema = z.object({
  // Vacío cuando el dominio ya identifica a la distribuidora (ver login-schema).
  tenant_slug: z
    .string()
    .trim()
    .refine(
      (value) => value === "" || /^[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*$/.test(value),
      "Solo letras, números y guiones",
    ),
  client_type: z.enum(["individual", "company"]),
  name: z
    .string()
    .trim()
    .min(2, "Ingresá tu nombre o el de tu comercio")
    .max(255, "Máximo 255 caracteres"),
  email: z.email("Email inválido"),
  phone: z
    .string()
    .trim()
    .min(8, "Ingresá un teléfono / WhatsApp válido")
    .max(50, "Máximo 50 caracteres"),
  tax_id: z.string().trim().max(50, "Máximo 50 caracteres"),
  password: z
    .string()
    .min(6, "Mínimo 6 caracteres")
    .max(255, "Máximo 255 caracteres"),
});

export type ClientRegisterSchema = z.infer<typeof clientRegisterSchema>;
