"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { PLATFORM_NAME } from "@/constants/brand";
import { PlatformLoginForm } from "@/features/platform/components/platform-login-form";
import { usePlatformSession } from "@/features/platform/hooks/use-platform-auth";

export default function PlatformLoginPage() {
  const router = useRouter();
  const { data, isLoading } = usePlatformSession();

  // Si ya tiene sesión de plataforma, no tiene sentido mostrarle el login.
  useEffect(() => {
    if (!isLoading && data) router.replace("/platform/tenants");
  }, [data, isLoading, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <div className="w-full max-w-sm rounded-3xl bg-card p-7 ring-[1.5px] ring-border">
        <div className="mb-6 border-b pb-5">
          <span className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-forest font-heading text-sm font-extrabold text-forest-foreground">
              P
            </span>
            <span className="font-heading text-base font-bold">{PLATFORM_NAME}</span>
          </span>
          <p className="mt-1.5 text-xs text-muted-foreground">Administración de la plataforma</p>
        </div>

        <h1 className="mb-1 text-2xl font-bold">Bienvenido</h1>
        <p className="mb-6 text-sm text-muted-foreground">
          Ingresá con tu cuenta de administrador para gestionar las distribuidoras.
        </p>

        <PlatformLoginForm />
      </div>
    </div>
  );
}
