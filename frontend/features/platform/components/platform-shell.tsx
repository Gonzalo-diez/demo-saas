"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Building2, LogOut, ShieldCheck, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { PLATFORM_NAME } from "@/constants/brand";
import { usePlatformLogout } from "@/features/platform/hooks/use-platform-auth";
import { usePlatformAuthStore } from "@/features/platform/store/platform-auth-store";

type PlatformNavItem = { href: string; label: string; icon: LucideIcon };

const PLATFORM_NAV: PlatformNavItem[] = [
  { href: "/platform/tenants", label: "Distribuidoras", icon: Building2 },
  { href: "/platform/admins", label: "Administradores", icon: ShieldCheck },
];

function PlatformBrand() {
  return (
    <span className="flex min-w-0 items-center gap-2.5">
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand font-heading text-sm font-extrabold text-brand-foreground">
        P
      </span>
      <span className="min-w-0">
        <span className="block truncate font-heading text-base font-bold leading-tight">
          {PLATFORM_NAME}
        </span>
        <span className="block text-[11px] uppercase tracking-widest text-sidebar-foreground/60">
          Plataforma
        </span>
      </span>
    </span>
  );
}

export function PlatformShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const logout = usePlatformLogout();
  const admin = usePlatformAuthStore((state) => state.admin);

  const current = PLATFORM_NAV.find((item) => pathname.startsWith(item.href));

  return (
    <div className="min-h-screen bg-background lg:flex">
      {/* Sidebar desktop */}
      <aside className="hidden w-60 shrink-0 flex-col bg-sidebar text-sidebar-foreground lg:sticky lg:top-0 lg:flex lg:h-screen">
        <div className="border-b border-sidebar-border px-3 py-4">
          <PlatformBrand />
        </div>

        <nav className="flex-1 space-y-0.5 p-2 pt-3">
          {PLATFORM_NAV.map((item) => {
            const isActive = pathname.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-sidebar-primary font-semibold text-sidebar-primary-foreground"
                    : "text-sidebar-foreground/75 hover:bg-sidebar-accent hover:text-sidebar-foreground",
                )}
              >
                <Icon className="size-4 shrink-0" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-sidebar-border p-2">
          {admin && (
            <p className="truncate px-3 pb-1 pt-1 text-xs text-sidebar-foreground/60">
              {admin.email}
            </p>
          )}
          <button
            type="button"
            onClick={() => logout.mutate()}
            disabled={logout.isPending}
            className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-sidebar-foreground/75 transition-colors hover:bg-sidebar-accent hover:text-kraft disabled:opacity-50"
          >
            <LogOut className="size-4 shrink-0" />
            {logout.isPending ? "Saliendo..." : "Cerrar sesión"}
          </button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Header mobile: marca + navegación */}
        <header className="sticky top-0 z-30 border-b bg-background/90 backdrop-blur">
          <div className="flex h-14 items-center justify-between gap-3 px-4 lg:h-16 lg:px-8">
            <h1 className="truncate text-lg font-bold sm:text-xl">
              {current?.label ?? "Plataforma"}
            </h1>
            <button
              type="button"
              onClick={() => logout.mutate()}
              disabled={logout.isPending}
              className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground lg:hidden"
            >
              <LogOut className="size-4" />
              Salir
            </button>
          </div>

          <nav className="flex gap-1 overflow-x-auto border-t px-3 py-2 lg:hidden">
            {PLATFORM_NAV.map((item) => {
              const isActive = pathname.startsWith(item.href);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "inline-flex shrink-0 items-center gap-2 rounded-xl px-3 py-1.5 text-sm font-medium",
                    isActive ? "bg-forest text-forest-foreground" : "text-muted-foreground",
                  )}
                >
                  <Icon className="size-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
