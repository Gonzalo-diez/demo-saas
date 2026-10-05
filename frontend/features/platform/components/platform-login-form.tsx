"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  platformLoginSchema,
  type PlatformLoginSchema,
} from "@/features/platform/schemas/platform-schemas";
import { usePlatformLogin } from "@/features/platform/hooks/use-platform-auth";

const inputCls =
  "w-full rounded-xl border border-input bg-card px-3 py-2.5 text-sm outline-none transition-colors placeholder:text-muted-foreground focus:ring-2 focus:ring-ring/50";

export function PlatformLoginForm() {
  const login = usePlatformLogin();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PlatformLoginSchema>({
    resolver: zodResolver(platformLoginSchema),
    defaultValues: { email: "", password: "" },
  });

  return (
    <form onSubmit={handleSubmit((data) => login.mutate(data))} className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="email">Email</Label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          placeholder="admin@plataforma.com"
          {...register("email")}
          className={inputCls}
        />
        {errors.email && (
          <p className="text-xs font-medium text-destructive">{errors.email.message}</p>
        )}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="password">Contraseña</Label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          placeholder="••••••••"
          {...register("password")}
          className={inputCls}
        />
        {errors.password && (
          <p className="text-xs font-medium text-destructive">{errors.password.message}</p>
        )}
      </div>

      {login.error && (
        <p className="rounded-xl bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">
          {login.error instanceof Error ? login.error.message : "Error al iniciar sesión"}
        </p>
      )}

      <Button type="submit" className="w-full" disabled={login.isPending}>
        {login.isPending ? "Ingresando..." : "Ingresar"}
      </Button>
    </form>
  );
}
