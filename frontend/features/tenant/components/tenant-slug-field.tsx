"use client";

import { useEffect } from "react";
import { Label } from "@/components/ui/label";
import { useTenantStore } from "@/features/tenant/store/tenant-store";
import { useTenantPreview } from "@/features/tenant/hooks/use-tenant-branding";

type Props = {
  value: string;
  onChange: (value: string) => void;
  error?: string;
  inputClassName: string;
};

/**
 * Campo "Distribuidora" de los logins.
 *
 * - En el dominio de una distribuidora (tienda.distri-oeste.com) NO se pide nada:
 *   ya se sabe a cuál se entra, solo se lo confirma.
 * - En localhost o en el dominio de la plataforma se escribe el código; se completa
 *   solo con el último usado (o ?tenant= / .env) y muestra a cuál se va a entrar.
 */
export function TenantSlugField({ value, onChange, error, inputClassName }: Props) {
  const storedSlug = useTenantStore((state) => state.slug);
  const hostTenant = useTenantStore((state) => state.hostTenant);
  const hostChecked = useTenantStore((state) => state.hostChecked);
  const { tenant, isChecking, notFound } = useTenantPreview(value);

  // Cuando el store termina de hidratarse, precargamos el slug si el campo está vacío.
  useEffect(() => {
    if (storedSlug && !value) onChange(storedSlug);
    // solo reaccionamos a que llegue el slug guardado
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storedSlug]);

  if (!hostChecked) {
    // Esperamos a saber si el dominio identifica a la distribuidora (evita parpadeo).
    return <div className="h-[72px]" aria-hidden />;
  }

  if (hostTenant) {
    return (
      <p className="rounded-xl bg-muted/60 px-3 py-2 text-xs font-medium text-forest dark:text-brand">
        Ingresás a {hostTenant.name}
      </p>
    );
  }

  return (
    <div className="space-y-1.5">
      <Label htmlFor="tenant_slug">Distribuidora</Label>
      <input
        id="tenant_slug"
        type="text"
        autoComplete="organization"
        autoCapitalize="none"
        spellCheck={false}
        placeholder="mi-distribuidora"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className={inputClassName}
      />
      {error ? (
        <p className="text-xs font-medium text-destructive">{error}</p>
      ) : tenant ? (
        <p className="text-xs font-medium text-forest dark:text-brand">
          Ingresás a {tenant.name}
        </p>
      ) : notFound ? (
        <p className="text-xs font-medium text-destructive">
          No encontramos esa distribuidora. Revisá el código.
        </p>
      ) : (
        <p className="text-xs text-muted-foreground">
          {isChecking ? "Buscando..." : "El código te lo da tu distribuidora."}
        </p>
      )}
    </div>
  );
}
