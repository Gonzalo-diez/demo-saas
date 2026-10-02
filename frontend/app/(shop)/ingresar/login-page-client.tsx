"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ClientLoginForm } from "@/features/shop/auth/components/login-form";
import { useClientSession } from "@/features/shop/auth/hooks/use-session";

export function LoginPageClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("redirect") || "/catalogo";

  // Si ya tiene sesión, no tiene sentido mostrarle el login de nuevo.
  const { data, isLoading } = useClientSession();
  useEffect(() => {
    if (!isLoading && data) {
      router.replace(redirectTo);
    }
  }, [data, isLoading, redirectTo, router]);

  return (
    <div className="flex min-h-[80vh] items-center justify-center bg-muted/50 p-6">
      <div className="w-full max-w-sm rounded-xl border bg-background p-6 shadow-sm">
        <div className="mb-6 flex items-center gap-2.5 border-b pb-5">
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--brand)] text-xs font-bold text-[var(--brand-foreground)]">
            DC
          </span>
          <div>
            <p className="text-sm font-semibold leading-none">Distri Choco</p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Catálogo mayorista
            </p>
          </div>
        </div>

        <h1 className="mb-1 text-xl font-semibold">Bienvenido</h1>
        <p className="mb-6 text-sm text-muted-foreground">
          Ingresá con tu cuenta de cliente para ver el catálogo y hacer tu
          pedido.
        </p>

        <ClientLoginForm redirectTo={redirectTo} />
      </div>
    </div>
  );
}