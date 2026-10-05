"use client";

import { cn } from "@/lib/utils";
import { useTenantBranding } from "@/features/tenant/hooks/use-tenant-branding";

type MarkProps = {
  name: string;
  initials: string;
  logoUrl?: string | null;
  className?: string;
};

/** Cuadrado con el logo de la distribuidora (o sus iniciales si no cargó uno). */
export function TenantMark({ name, initials, logoUrl, className }: MarkProps) {
  if (logoUrl) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={logoUrl}
        alt={name}
        className={cn("shrink-0 rounded-xl bg-card object-contain", className)}
      />
    );
  }

  return (
    <span
      className={cn(
        "flex shrink-0 items-center justify-center rounded-xl bg-brand font-heading font-extrabold text-brand-foreground",
        className,
      )}
    >
      {initials}
    </span>
  );
}

/** Solo el nombre de la distribuidora actual (para textos corridos). */
export function TenantName() {
  const { name } = useTenantBranding();
  return <>{name}</>;
}

type BrandProps = {
  className?: string;
  markClassName?: string;
  nameClassName?: string;
  hideName?: boolean;
};

/** Marca + nombre de la distribuidora actual. */
export function TenantBrand({
  className,
  markClassName,
  nameClassName,
  hideName,
}: BrandProps) {
  const { name, initials, logoUrl } = useTenantBranding();

  return (
    <span className={cn("flex min-w-0 items-center gap-2.5", className)}>
      <TenantMark
        name={name}
        initials={initials}
        logoUrl={logoUrl}
        className={cn("h-9 w-9 text-sm", markClassName)}
      />
      {!hideName && (
        <span className={cn("truncate font-heading text-base font-bold", nameClassName)}>
          {name}
        </span>
      )}
    </span>
  );
}
