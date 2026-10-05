"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { ClientLoginForm } from "@/features/shop/auth/components/login-form";
import { ClientRegisterForm } from "@/features/shop/auth/components/register-form";

export type AuthMode = "register" | "login";

type Props = {
  /** Pestaña con la que arranca. */
  defaultMode?: AuthMode;
  /** A dónde ir al terminar. `null`: quedarse en la página (checkout). */
  redirectTo?: string | null;
};

/**
 * "Crear cuenta" / "Ya tengo cuenta". Se usa en /ingresar y en el checkout: ahí es
 * donde se le pide la cuenta al visitante, recién al finalizar la compra.
 */
export function ClientAuthPanel({ defaultMode = "register", redirectTo = null }: Props) {
  const [mode, setMode] = useState<AuthMode>(defaultMode);

  const tab = (value: AuthMode, label: string) => (
    <button
      type="button"
      role="tab"
      aria-selected={mode === value}
      onClick={() => setMode(value)}
      className={cn(
        "flex-1 rounded-lg px-3 py-2 text-sm font-semibold transition-colors",
        mode === value
          ? "bg-card text-foreground shadow-sm"
          : "text-muted-foreground hover:text-foreground",
      )}
    >
      {label}
    </button>
  );

  return (
    <div className="space-y-5">
      <div role="tablist" className="flex gap-1 rounded-xl bg-muted p-1">
        {tab("register", "Crear cuenta")}
        {tab("login", "Ya tengo cuenta")}
      </div>

      {mode === "register" ? (
        <ClientRegisterForm
          redirectTo={redirectTo}
          onAlreadyRegistered={() => setMode("login")}
        />
      ) : (
        <ClientLoginForm redirectTo={redirectTo} />
      )}
    </div>
  );
}
