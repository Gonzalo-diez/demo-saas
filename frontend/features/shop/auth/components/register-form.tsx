"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  clientRegisterSchema,
  type ClientRegisterSchema,
} from "@/features/shop/auth/schemas/register-schema";
import { useClientRegister } from "@/features/shop/auth/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { TenantSlugField } from "@/features/tenant/components/tenant-slug-field";
import { useTenantStore } from "@/features/tenant/store/tenant-store";

type Props = {
  /** A dónde ir al registrarse. `null`: quedarse en la página (checkout). */
  redirectTo?: string | null;
  /** Se llama si el email ya tiene cuenta, para ofrecer "Ya tengo cuenta". */
  onAlreadyRegistered?: () => void;
};

export function ClientRegisterForm({ redirectTo = null, onAlreadyRegistered }: Props) {
  const registerClient = useClientRegister(redirectTo);
  const hostTenant = useTenantStore((state) => state.hostTenant);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    setError,
    formState: { errors },
  } = useForm<ClientRegisterSchema>({
    resolver: zodResolver(clientRegisterSchema),
    defaultValues: {
      tenant_slug: "",
      client_type: "company",
      name: "",
      email: "",
      phone: "",
      tax_id: "",
      password: "",
    },
  });

  const onSubmit = (data: ClientRegisterSchema) => {
    // En el dominio de la distribuidora no hace falta código; en los demás, sí.
    if (!hostTenant && !data.tenant_slug) {
      setError("tenant_slug", { message: "Ingresá el código de tu distribuidora" });
      return;
    }
    registerClient.mutate(data);
  };

  const inputCls =
    "w-full rounded-xl border border-input bg-card px-3 py-2.5 text-sm outline-none transition-colors placeholder:text-muted-foreground focus:ring-2 focus:ring-ring/50";

  const errorMessage =
    registerClient.error instanceof Error
      ? registerClient.error.message
      : registerClient.error
        ? "No pudimos crear tu cuenta. Intentá de nuevo."
        : null;
  // El backend responde 409 con este texto cuando el email ya existe.
  const alreadyRegistered = !!errorMessage && /ya existe una cuenta/i.test(errorMessage);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
      <TenantSlugField
        value={watch("tenant_slug")}
        onChange={(value) =>
          setValue("tenant_slug", value, { shouldValidate: !!errors.tenant_slug })
        }
        error={errors.tenant_slug?.message}
        inputClassName={inputCls}
      />

      <div className="space-y-1.5">
        <Label htmlFor="register-client-type">Soy</Label>
        <select
          id="register-client-type"
          {...register("client_type")}
          className={inputCls}
        >
          <option value="company">Un comercio / empresa</option>
          <option value="individual">Una persona</option>
        </select>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="register-name">Nombre o razón social</Label>
        <input
          id="register-name"
          autoComplete="name"
          placeholder="Ej: Kiosco Don Juan"
          {...register("name")}
          className={inputCls}
        />
        {errors.name && (
          <p className="text-xs font-medium text-destructive">{errors.name.message}</p>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="register-email">Email</Label>
          <input
            id="register-email"
            type="email"
            autoComplete="email"
            placeholder="tu@email.com"
            {...register("email")}
            className={inputCls}
          />
          {errors.email && (
            <p className="text-xs font-medium text-destructive">{errors.email.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="register-phone">WhatsApp / teléfono</Label>
          <input
            id="register-phone"
            type="tel"
            autoComplete="tel"
            placeholder="Ej: 3751123456"
            {...register("phone")}
            className={inputCls}
          />
          {errors.phone && (
            <p className="text-xs font-medium text-destructive">{errors.phone.message}</p>
          )}
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="register-tax-id">CUIT (opcional)</Label>
        <input
          id="register-tax-id"
          inputMode="numeric"
          placeholder="Ej: 20-12345678-9"
          {...register("tax_id")}
          className={inputCls}
        />
        {errors.tax_id && (
          <p className="text-xs font-medium text-destructive">{errors.tax_id.message}</p>
        )}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="register-password">Contraseña</Label>
        <input
          id="register-password"
          type="password"
          autoComplete="new-password"
          placeholder="Mínimo 6 caracteres"
          {...register("password")}
          className={inputCls}
        />
        {errors.password && (
          <p className="text-xs font-medium text-destructive">{errors.password.message}</p>
        )}
      </div>

      {errorMessage && (
        <div className="space-y-2 rounded-xl bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">
          <p>{errorMessage}</p>
          {alreadyRegistered && onAlreadyRegistered && (
            <button
              type="button"
              onClick={onAlreadyRegistered}
              className="underline underline-offset-2"
            >
              Ir a iniciar sesión
            </button>
          )}
        </div>
      )}

      <Button type="submit" className="w-full" disabled={registerClient.isPending}>
        {registerClient.isPending ? "Creando tu cuenta..." : "Crear cuenta y continuar"}
      </Button>
    </form>
  );
}
