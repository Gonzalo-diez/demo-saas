import type { Metadata } from "next";
import { Toaster } from "@/components/ui/sonner"
import { QueryProvider } from "@/providers/query-provider";
import { Instrument_Sans, JetBrains_Mono, Bricolage_Grotesque } from "next/font/google";
import { TenantHydrator } from "@/features/tenant/components/tenant-hydrator";
import { PLATFORM_NAME } from "@/constants/brand";
import "./globals.css";
import { cn } from "@/lib/utils";

const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' });

// Texto de uso diario
const instrumentSans = Instrument_Sans({
  variable: "--font-ui",
  subsets: ["latin"],
});

// Títulos y números destacados
const bricolage = Bricolage_Grotesque({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["500", "700", "800"],
});

export const metadata: Metadata = {
  title: `${PLATFORM_NAME} - Catálogo mayorista`,
  description:
    "Catálogo mayorista online para distribuidoras: pedidos rápidos, clientes B2B y gestión de ventas, stock y reparto.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="es"
      className={cn(
        "h-full",
        "antialiased",
        instrumentSans.variable,
        jetbrainsMono.variable,
        bricolage.variable,
      )}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col">
        <QueryProvider>
          <TenantHydrator />
          {children}
          <Toaster richColors position="top-right" />
        </QueryProvider>
      </body>
    </html>
  );
}