"use client";

import { useEffect, useState, type ReactNode } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  tenantSchema,
  type TenantFormValues,
} from "@/features/platform/schemas/platform-schemas";
import { useCreateTenant, useUpdateTenant } from "@/features/platform/hooks/use-tenants";
import type { Tenant } from "@/features/platform/types";
import { extractHost, slugify } from "@/lib/slugify";
import { env } from "@/lib/env";

type TenantFormProps = { tenant?: Tenant | null; onDone: () => void };

function Field({
  label,
  error,
  hint,
  children,
}: {
  label: string;
  error?: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      {children}
      {error ? (
        <p className="text-sm text-destructive">{error}</p>
      ) : hint ? (
        <p className="text-xs text-muted-foreground">{hint}</p>
      ) : null}
    </div>
  );
}

function TenantForm({ tenant, onDone }: TenantFormProps) {
  const createTenant = useCreateTenant();
  const updateTenant = useUpdateTenant();
  const isEdit = !!tenant;
  const isPending = createTenant.isPending || updateTenant.isPending;

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, dirtyFields },
  } = useForm<TenantFormValues>({
    resolver: zodResolver(tenantSchema),
    defaultValues: {
      name: tenant?.name ?? "",
      slug: tenant?.slug ?? "",
      domain: tenant?.domain ?? "",
      email: tenant?.email ?? "",
      logo_url: tenant?.logo_url ?? "",
      admin_name: "",
      admin_email: "",
      admin_password: "",
    },
  });

  const domainValue = watch("domain");
  const domainHost = extractHost(domainValue ?? "");
  const domainEdited = !!dirtyFields.domain;
  const slugValue = watch("slug");

  // Entorno de pruebas: al crear, el dominio se propone solo (<codigo>.localhost) hasta que
  // lo editen a mano. Cada distribuidora queda con su propia URL local, sin tocar el hosts.
  useEffect(() => {
    if (isEdit || domainEdited || !env.tenantDomainSuffix) return;
    setValue("domain", slugValue ? `${slugValue}${env.tenantDomainSuffix}` : "");
  }, [slugValue, isEdit, domainEdited, setValue]);

  // URL con la que se va a abrir la tienda (en *.localhost: http y con el puerto del dev server).
  const isLocalDomain = domainHost === "localhost" || domainHost.endsWith(".localhost");
  const storeUrl = domainHost
    ? isLocalDomain
      ? `http://${domainHost}${typeof window !== "undefined" && window.location.port ? `:${window.location.port}` : ""}`
      : `https://${domainHost}`
    : "";

  // Al crear, el código se arma solo a partir del nombre hasta que lo editen a mano.
  const name = watch("name");
  const slugEdited = !!dirtyFields.slug;
  useEffect(() => {
    if (!isEdit && !slugEdited) setValue("slug", slugify(name));
  }, [name, isEdit, slugEdited, setValue]);

  const onSubmit = async (values: TenantFormValues) => {
    try {
      if (tenant) {
        await updateTenant.mutateAsync({
          tenantId: tenant.id,
          data: {
            name: values.name,
            slug: values.slug,
            domain: values.domain,
            email: values.email || null,
            logo_url: values.logo_url || null,
          },
        });
      } else {
        await createTenant.mutateAsync({
          name: values.name,
          slug: values.slug,
          domain: values.domain,
          email: values.email || null,
          logo_url: values.logo_url || null,
          ...(values.admin_email
            ? {
                admin_name: values.admin_name || null,
                admin_email: values.admin_email,
                admin_password: values.admin_password,
              }
            : {}),
        });
      }
      onDone();
    } catch {
      // el toast de error lo muestra el hook
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Nombre *" error={errors.name?.message}>
          <Input placeholder="Distribuidora Oeste" {...register("name")} />
        </Field>
        <Field
          label="Código *"
          error={errors.slug?.message}
          hint={
            isEdit
              ? "Identifica a la distribuidora en la plataforma. El ingreso de tus clientes y vendedores es por el dominio."
              : "Identificador interno. Se genera solo desde el nombre."
          }
        >
          <Input placeholder="distribuidora-oeste" {...register("slug")} />
        </Field>
        <div className="sm:col-span-2">
          <Field
            label="Dominio o URL de la tienda *"
            error={errors.domain?.message}
            hint={
              storeUrl
                ? `La tienda de esta distribuidora se abrirá en ${storeUrl}`
                : "Pegá el dominio o la URL (ej: tienda.midistribuidora.com). Se guarda solo el dominio."
            }
          >
            <Input
              placeholder="tienda.distribuidora-oeste.com"
              autoCapitalize="none"
              spellCheck={false}
              {...register("domain")}
            />
          </Field>
        </div>
        <Field label="Email de contacto" error={errors.email?.message}>
          <Input type="email" placeholder="ventas@distribuidora.com" {...register("email")} />
        </Field>
        <Field label="URL del logo" error={errors.logo_url?.message} hint="Opcional. Si no, se usan las iniciales.">
          <Input placeholder="https://..." {...register("logo_url")} />
        </Field>
      </div>

      {!isEdit && (
        <div className="space-y-4 rounded-2xl border bg-muted/40 p-4">
          <div>
            <h4 className="text-sm font-semibold">Primer administrador</h4>
            <p className="text-xs text-muted-foreground">
              Es el dueño de la distribuidora: entra al panel y crea a sus vendedores. Podés dejarlo
              vacío y crearlo después.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Nombre" error={errors.admin_name?.message}>
              <Input placeholder="Nombre del dueño" {...register("admin_name")} />
            </Field>
            <Field label="Email" error={errors.admin_email?.message}>
              <Input type="email" autoComplete="off" placeholder="dueno@distribuidora.com" {...register("admin_email")} />
            </Field>
            <Field label="Contraseña" error={errors.admin_password?.message}>
              <Input type="password" autoComplete="new-password" placeholder="Mínimo 6 caracteres" {...register("admin_password")} />
            </Field>
          </div>
        </div>
      )}

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onDone} disabled={isPending}>
          Cancelar
        </Button>
        <Button type="submit" disabled={isPending}>
          {isPending ? "Guardando..." : isEdit ? "Guardar cambios" : "Crear distribuidora"}
        </Button>
      </div>
    </form>
  );
}

type TenantFormDialogProps = {
  tenant?: Tenant | null;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  trigger?: ReactNode;
};

export function TenantFormDialog({ tenant, open: controlledOpen, onOpenChange, trigger }: TenantFormDialogProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const open = controlledOpen ?? internalOpen;
  const setOpen = onOpenChange ?? setInternalOpen;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      {trigger && <DialogTrigger asChild>{trigger}</DialogTrigger>}
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{tenant ? "Editar distribuidora" : "Nueva distribuidora"}</DialogTitle>
          <DialogDescription>
            Cada distribuidora tiene sus propios usuarios, productos, clientes y pedidos.
          </DialogDescription>
        </DialogHeader>
        <TenantForm tenant={tenant} onDone={() => setOpen(false)} />
      </DialogContent>
    </Dialog>
  );
}
