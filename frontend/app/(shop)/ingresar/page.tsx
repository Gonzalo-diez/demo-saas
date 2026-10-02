import type { Metadata } from "next";
import { Suspense } from "react";
import { LoginPageClient } from "@/app/(shop)/ingresar/login-page-client";

export async function generateMetadata(): Promise<Metadata> {
  return {
    title: "Ingresar | Distri Choco",
    description: "Iniciá sesión para ver el catálogo y hacer tu pedido.",
  };
}

export default function IngresarPage() {
  return (
    <Suspense fallback={null}>
      <LoginPageClient />
    </Suspense>
  );
}