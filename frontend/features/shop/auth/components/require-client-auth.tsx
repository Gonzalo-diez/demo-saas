"use client";

import { useEffect } from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useClientSession } from "@/features/shop/auth/hooks/use-session";

/**
 * Envuelve el catálogo y el checkout: solo un cliente logueado puede
 * verlos. Si no hay sesión, redirige a /ingresar guardando la página
 * a la que quería entrar para volver ahí después del login.
 */
export function RequireClientAuth({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { data, isLoading, isError } = useClientSession();

  useEffect(() => {
    if (!isLoading && (isError || !data)) {
      const query = searchParams.toString();
      const currentUrl = query ? `${pathname}?${query}` : pathname;
      router.replace(`/ingresar?redirect=${encodeURIComponent(currentUrl)}`);
    }
  }, [data, isError, isLoading, pathname, router, searchParams]);

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-sm text-muted-foreground">Cargando...</p>
      </div>
    );
  }

  if (isError || !data) {
    return null;
  }

  return <>{children}</>;
}