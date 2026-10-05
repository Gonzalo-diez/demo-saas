import { z } from "zod";
import { SLUG_REGEX, extractHost, isValidDomainHost } from "@/lib/slugify";

export const platformLoginSchema = z.object({
  email: z.email("Email inválido"),
  password: z.string().min(1, "La contraseña es obligatoria"),
});
export type PlatformLoginSchema = z.infer<typeof platformLoginSchema>;

const optionalEmail = z.union([z.literal(""), z.email("Email inválido")]);
const optionalUrl = z.union([z.literal(""), z.url("Debe ser una URL válida")]);

export const tenantSchema = z
  .object({
    name: z.string().trim().min(1, "El nombre es obligatorio").max(255),
    slug: z
      .string()
      .trim()
      .toLowerCase()
      .min(1, "El código es obligatorio")
      .max(100)
      .regex(SLUG_REGEX, "Solo minúsculas, números y guiones (ej: distri-oeste)"),
    // Dominio o URL de la tienda: se acepta "tienda.x.com" o "https://tienda.x.com/..."
    // y el backend guarda solo el host.
    domain: z
      .string()
      .trim()
      .min(1, "El dominio o URL de la tienda es obligatorio")
      .max(255)
      .refine(
        (value) => isValidDomainHost(extractHost(value)),
        "Dominio no válido (ej: tienda.midistribuidora.com). No uses una IP.",
      ),
    email: optionalEmail,
    logo_url: optionalUrl,
    // Primer administrador de la distribuidora (opcional; email y clave van juntos)
    admin_name: z.string().trim().max(255),
    admin_email: optionalEmail,
    admin_password: z.union([z.literal(""), z.string().min(6, "Mínimo 6 caracteres")]),
  })
  .superRefine((data, ctx) => {
    if (!!data.admin_email !== !!data.admin_password) {
      ctx.addIssue({
        code: "custom",
        path: [data.admin_email ? "admin_password" : "admin_email"],
        message: "Completá email y contraseña del administrador (o dejá ambos vacíos)",
      });
    }
  });
export type TenantFormValues = z.infer<typeof tenantSchema>;

export const platformAdminSchema = z.object({
  name: z.string().trim().min(1, "El nombre es obligatorio").max(255),
  email: z.email("Email inválido"),
  password: z.string().min(6, "Mínimo 6 caracteres").max(255),
});
export type PlatformAdminFormValues = z.infer<typeof platformAdminSchema>;
