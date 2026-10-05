import type { NextConfig } from "next"

// Destino del proxy de /api (solo se usa si NEXT_PUBLIC_API_URL está vacío).
const apiProxyTarget = process.env.API_PROXY_TARGET ?? "http://localhost:8000"

const nextConfig: NextConfig = {
  // Desarrollo: permite abrir el dev server con las URLs locales de cada distribuidora
  // (distri-norte.localhost:3000, etc.). No afecta a producción.
  allowedDevOrigins: ["*.localhost"],

  // El backend usa URLs con barra final (/api/categories/): Next no debe quitársela
  // con un redirect antes de reenviarlas, porque FastAPI la vuelve a agregar y el
  // navegador terminaría llamando directo al backend (sin cookies del dominio).
  skipTrailingSlashRedirect: true,

  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "res.cloudinary.com",
      },
    ],
  },

  // Cada distribuidora entra con su propio dominio (tienda.distri-oeste.com). Las cookies
  // de sesión son por dominio, así que lo más simple es que el navegador llame a /api en el
  // MISMO dominio de la tienda y Next lo reenvíe al backend. Para activarlo, dejar
  // NEXT_PUBLIC_API_URL vacío (ver .env.example).
  async rewrites() {
    return [
      // Con barra final (/api/categories/): se reenvía tal cual. Sin esta regla, Next
      // la pierde en `:path*` y FastAPI responde un 307 hacia su propio host.
      {
        source: "/api/:path*/",
        destination: `${apiProxyTarget}/api/:path*/`,
      },
      {
        source: "/api/:path*",
        destination: `${apiProxyTarget}/api/:path*`,
      },
    ]
  },
}

export default nextConfig
