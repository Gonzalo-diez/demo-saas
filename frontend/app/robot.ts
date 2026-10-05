import type { MetadataRoute } from "next";
import { env } from "@/lib/env";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: [
          // Panel de administración: no aporta nada indexado y además
          // está detrás de login, pero igual conviene que ni lo pise
          // un crawler (evita que quede el título "Login" indexado).
          "/admin",
          "/login",
          "/platform",

          // Login/registro de clientes de la tienda.
          "/ingresar",

          // El catálogo (/catalogo) es público y SÍ se indexa. Ojo: se renderiza en
          // el cliente con los datos de la distribuidora del dominio.

          // Checkout: formularios con datos personales, cero valor SEO.
          "/checkout",

          // Seguimiento/edición de pedidos: la URL incluye un token
          // privado del pedido, no debe quedar indexada bajo ningún
          // concepto.
          "/order",
        ],
      },
    ],
    sitemap: `${env.siteUrl}/sitemap.xml`,
  };
}