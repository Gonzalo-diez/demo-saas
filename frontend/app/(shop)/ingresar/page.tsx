import type { Metadata } from "next";
import { Suspense } from "react";
import { LoginPageClient } from "@/app/(shop)/ingresar/login-page-client";

export async function generateMetadata(): Promise<Metadata> {
  return {
    title: "Ingresar",
    description: "Ingresá o creá tu cuenta para hacer tu pedido.",
  };
}

export default function IngresarPage() {
  return (
    <Suspense fallback={null}>
      <LoginPageClient />
    </Suspense>
  );
}