import { z } from "zod";

export const loginSchema = z.object({
  // Vacío cuando el dominio ya identifica a la distribuidora; en localhost / dominio
  // de la plataforma el formulario lo exige antes de enviar.
  tenant_slug: z
    .string()
    .trim()
    .refine(
      (value) => value === "" || /^[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*$/.test(value),
      "Solo letras, números y guiones",
    ),
  email: z.email("Email inválido"),
  password: z.string().min(1, "La contraseña es obligatoria"),
});

export type LoginSchema = z.infer<typeof loginSchema>;