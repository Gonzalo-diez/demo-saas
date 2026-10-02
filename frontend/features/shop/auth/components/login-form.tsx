"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  clientLoginSchema,
  type ClientLoginSchema,
} from "@/features/shop/auth/schemas/login-schema";
import { useClientLogin } from "@/features/shop/auth/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

type Props = {
  redirectTo?: string;
};

export function ClientLoginForm({ redirectTo }: Props) {
  const login = useClientLogin(redirectTo);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ClientLoginSchema>({
    resolver: zodResolver(clientLoginSchema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = (data: ClientLoginSchema) => {
    login.mutate(data);
  };

  const inputCls =
    "w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm outline-none transition-colors placeholder:text-muted-foreground focus:ring-2 focus:ring-ring/50";

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="email">Email</Label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          placeholder="tu@email.com"
          {...register("email")}
          className={inputCls}
        />
        {errors.email && (
          <p className="text-xs font-medium text-destructive">
            {errors.email.message}
          </p>
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
          <p className="text-xs font-medium text-destructive">
            {errors.password.message}
          </p>
        )}
      </div>

      {login.error && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">
          {login.error instanceof Error
            ? login.error.message
            : "No pudimos iniciar sesión. Revisá tus datos e intentá de nuevo."}
        </p>
      )}

      <Button type="submit" className="w-full" disabled={login.isPending}>
        {login.isPending ? "Ingresando..." : "Ingresar"}
      </Button>
    </form>
  );
}