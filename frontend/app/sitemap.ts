import type { MetadataRoute } from "next";
import { env } from "@/lib/env";

// El catálogo (/catalogo) y todo lo demás sigue atrás de login
// (RequireClientAuth), así que no tiene sentido listarlo acá: un
// crawler no ve contenido real ahí. Si en algún momento se abre el
// catálogo (o parte) sin login, sus páginas se agregan acá.
export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: env.siteUrl,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 1,
    },
  ];
}