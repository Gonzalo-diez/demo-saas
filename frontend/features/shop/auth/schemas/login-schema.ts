import { z } from "zod";

export const clientLoginSchema = z.object({
  email: z.email("Email inválido"),
  password: z.string().min(1, "La contraseña es obligatoria"),
});

export type ClientLoginSchema = z.infer<typeof clientLoginSchema>;