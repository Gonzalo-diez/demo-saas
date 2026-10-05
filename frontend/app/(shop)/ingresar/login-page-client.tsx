"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ClientAuthPanel } from "@/features/shop/auth/components/auth-panel";
import { useClientSession } from "@/features/shop/auth/hooks/use-session";
import { TenantBrand } from "@/features/tenant/components/tenant-brand";

export function LoginPageClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("redirect") || "/catalogo";
  // /ingresar?modo=registro abre directo "Crear cuenta".
  const defaultMode = searchParams.get("modo") === "registro" ? "register" : "login";

  // Si ya tiene sesión, no tiene sentido mostrarle el login de nuevo.
  const { data, isLoading } = useClientSession();
  useEffect(() => {
    if (!isLoading && data) {
      router.replace(redirectTo);
    }
  }, [data, isLoading, redirectTo, router]);

  return (
    <div className="flex min-h-[80vh] items-center justify-center bg-background p-6">
      <div className="w-full max-w-md rounded-3xl bg-card p-7 ring-[1.5px] ring-border">
        <div className="mb-6 border-b pb-5">
          <TenantBrand />
          <p className="mt-1.5 text-xs text-muted-foreground">
            Catálogo mayorista
          </p>
        </div>

        <h1 className="mb-1 text-2xl font-bold">Tu cuenta</h1>
        <p className="mb-6 text-sm text-muted-foreground">
          Ingresá o creá tu cuenta para hacer tu pedido. Para mirar el catálogo
          no hace falta.
        </p>

        <ClientAuthPanel defaultMode={defaultMode} redirectTo={redirectTo} />
      </div>
    </div>
  );
}
