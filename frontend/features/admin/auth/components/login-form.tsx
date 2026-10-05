"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  loginSchema,
  type LoginSchema,
} from "@/features/admin/auth/schemas/login-schema";
import { useLogin } from "@/features/admin/auth/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { TenantSlugField } from "@/features/tenant/components/tenant-slug-field";
import { useTenantStore } from "@/features/tenant/store/tenant-store";

export function LoginForm() {
  const login = useLogin();
  const hostTenant = useTenantStore((state) => state.hostTenant);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    setError,
    formState: { errors },
  } = useForm<LoginSchema>({
    resolver: zodResolver(loginSchema),
    defaultValues: { tenant_slug: "", email: "", password: "" },
  });

  const onSubmit = (data: LoginSchema) => {
    // En el dominio de la distribuidora no hace falta código; en los demás, sí.
    if (!hostTenant && !data.tenant_slug) {
      setError("tenant_slug", { message: "Ingresá el código de tu distribuidora" });
      return;
    }
    login.mutate(data);
  };

  const inputCls =
    "w-full rounded-xl border border-input bg-card px-3 py-2.5 text-sm outline-none transition-colors placeholder:text-muted-foreground focus:ring-2 focus:ring-ring/50";

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <TenantSlugField
        value={watch("tenant_slug")}
        onChange={(value) =>
          setValue("tenant_slug", value, { shouldValidate: !!errors.tenant_slug })
        }
        error={errors.tenant_slug?.message}
        inputClassName={inputCls}
      />

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
        <p className="rounded-xl bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">
          {login.error instanceof Error
            ? login.error.message
            : "Error al iniciar sesión"}
        </p>
      )}

      <Button type="submit" className="w-full" disabled={login.isPending}>
        {login.isPending ? "Ingresando..." : "Ingresar"}
      </Button>
    </form>
  );
}