import type { MetadataRoute } from "next";
import { env } from "@/lib/env";

// El catálogo es público. Las categorías son de cada distribuidora y se cargan en el
// cliente, así que acá solo listamos las páginas fijas. Para indexar cada categoría
// habría que generar este sitemap por dominio (leyendo el host de la request).
export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: env.siteUrl,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 1,
    },
    {
      url: `${env.siteUrl}/catalogo`,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 0.8,
    },
  ];
}