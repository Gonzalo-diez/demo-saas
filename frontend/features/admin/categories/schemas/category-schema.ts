import { z } from "zod";

export const categorySchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "El nombre es obligatorio")
    .max(100, "Máximo 100 caracteres"),
  description: z.string().trim().max(500, "Máximo 500 caracteres"),
  // Vacío = sin imagen (solo se permite si la categoría es privada).
  image_url: z.string().trim(),
  is_public: z.boolean(),
  requires_age_verification: z.boolean(),
}).superRefine((data, ctx) => {
  // Igual que un producto: lo que se ve en el catálogo necesita imagen.
  if (data.is_public && !data.image_url) {
    ctx.addIssue({
      code: "custom",
      path: ["image_url"],
      message:
        "Para publicarla en el catálogo necesita una imagen. Subila o desmarcá \"Publicar en el catálogo\".",
    });
  }
});

export type CategoryFormValues = z.infer<typeof categorySchema>;
