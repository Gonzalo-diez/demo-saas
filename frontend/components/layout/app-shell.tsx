"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Fragment, useEffect, useMemo, useState, type ReactNode } from "react";
import { Menu, PanelLeftClose, PanelLeftOpen, X, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useLogout } from "@/features/admin/auth/hooks/use-auth";
import { NAV_ITEMS, PAGE_TITLES } from "@/constants/navigation";
// Importamos la campanita de notificaciones
import { NotificationBell } from "@/features/admin/notifications/components/notification-bell";
import { TenantBrand } from "@/features/tenant/components/tenant-brand";

type AppShellProps = { children: ReactNode };

const SIDEBAR_STORAGE_KEY = "app-sidebar-collapsed";

function SidebarContent({
  pathname,
  collapsed,
  onNavigate,
  onLogout,
  isLoggingOut,
}: {
  pathname: string;
  collapsed: boolean;
  onNavigate?: () => void;
  onLogout: () => void;
  isLoggingOut: boolean;
}) {
  return (
    <div className="flex h-full flex-col">
      {/* Logo */}
      <div
        className={cn(
          "flex shrink-0 items-center gap-3 border-b border-sidebar-border px-3 py-4",
          collapsed && "justify-center px-2",
        )}
      >
        <TenantBrand hideName={collapsed} />
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto p-2 pt-3">
        <div className="space-y-0.5">
          {NAV_ITEMS.map((item) => {
            const isActive =
              pathname === item.href || pathname.startsWith(`${item.href}/`);
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onNavigate}
                title={collapsed ? item.label : undefined}
                className={cn(
                  "flex items-center gap-3 rounded-xl text-sm font-medium transition-colors",
                  collapsed
                    ? "justify-center px-2 py-2.5"
                    : "justify-start px-3 py-2.5",
                  isActive
                    ? "bg-sidebar-primary font-semibold text-sidebar-primary-foreground"
                    : "text-sidebar-foreground/75 hover:bg-sidebar-accent hover:text-sidebar-foreground",
                )}
              >
                <Icon
                  className={cn("shrink-0", collapsed ? "size-5" : "size-4")}
                />
                {!collapsed && <span className="truncate">{item.label}</span>}
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Footer — logout */}
      <div
        className={cn(
          "shrink-0 border-t border-sidebar-border p-2",
          collapsed && "flex justify-center",
        )}
      >
        <button
          type="button"
          onClick={onLogout}
          disabled={isLoggingOut}
          title="Cerrar sesión"
          className={cn(
            "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-sidebar-foreground/75 transition-colors hover:bg-sidebar-accent hover:text-kraft disabled:opacity-50",
            collapsed && "w-auto justify-center px-2",
          )}
        >
          <LogOut className={cn("shrink-0", collapsed ? "size-5" : "size-4")} />
          {!collapsed && (
            <span>{isLoggingOut ? "Saliendo..." : "Cerrar sesión"}</span>
          )}
        </button>
      </div>
    </div>
  );
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const logout = useLogout();

  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const saved =
      typeof window !== "undefined"
        ? window.localStorage.getItem(SIDEBAR_STORAGE_KEY)
        : null;
    setCollapsed(saved === "true");
    setHydrated(true);
  }, []);

  const [prevPathname, setPrevPathname] = useState(pathname);
  if (pathname !== prevPathname) {
    setPrevPathname(pathname);
    setMobileOpen(false);
  }

  useEffect(() => {
    if (!hydrated || typeof window === "undefined") return;
    window.localStorage.setItem(SIDEBAR_STORAGE_KEY, String(collapsed));
  }, [collapsed, hydrated]);

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  const currentTitle = useMemo(
    () =>
      PAGE_TITLES[pathname] ||
      NAV_ITEMS.find((item) => pathname.startsWith(item.href))?.label ||
      "Panel interno",
    [pathname],
  );

  const CollapseIcon = collapsed ? PanelLeftOpen : PanelLeftClose;
  const handleLogout = () => logout.mutate();

  return (
    <div className="min-h-screen bg-background">
      <div className="flex min-h-screen">
        {/* Sidebar desktop */}
        <aside
          className={cn(
            "hidden bg-sidebar text-sidebar-foreground transition-[width] duration-200 lg:block lg:sticky lg:top-0 lg:h-screen lg:overflow-hidden",
            collapsed ? "w-[56px]" : "w-60",
          )}
        >
          <SidebarContent
            pathname={pathname}
            collapsed={collapsed}
            onLogout={handleLogout}
            isLoggingOut={logout.isPending}
          />
        </aside>

        {/* Drawer mobile */}
        {mobileOpen && (
          <Fragment>
            <button
              type="button"
              aria-label="Cerrar menú"
              className="fixed inset-0 z-40 bg-black/50 lg:hidden"
              onClick={() => setMobileOpen(false)}
            />
            <aside className="fixed inset-y-0 left-0 z-50 flex w-[72vw] max-w-64 flex-col bg-sidebar text-sidebar-foreground shadow-xl lg:hidden">
              <div className="flex items-center justify-between border-b border-sidebar-border px-3 py-3">
                <TenantBrand />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-foreground"
                  onClick={() => setMobileOpen(false)}
                  aria-label="Cerrar menú"
                >
                  <X className="size-4" />
                </Button>
              </div>
              <SidebarContent
                pathname={pathname}
                collapsed={false}
                onNavigate={() => setMobileOpen(false)}
                onLogout={handleLogout}
                isLoggingOut={logout.isPending}
              />
            </aside>
          </Fragment>
        )}

        {/* Contenido principal */}
        <div className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-30 border-b bg-background/90 backdrop-blur">
            <div className="flex h-14 min-w-0 items-center justify-between px-3 sm:px-4 lg:h-16 lg:px-5">
              {/* Lado izquierdo: Botones y Título */}
              <div className="flex min-w-0 items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  className="shrink-0 lg:hidden"
                  onClick={() => setMobileOpen(true)}
                  aria-label="Abrir menú"
                >
                  <Menu className="size-4" />
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  className="hidden shrink-0 lg:inline-flex"
                  onClick={() => setCollapsed((prev) => !prev)}
                  aria-label={collapsed ? "Expandir sidebar" : "Colapsar sidebar"}
                  title={collapsed ? "Expandir sidebar" : "Colapsar sidebar"}
                >
                  <CollapseIcon className="size-4" />
                </Button>

                <h1 className="truncate text-lg font-bold sm:text-xl">
                  {currentTitle}
                </h1>
              </div>

              {/* Lado derecho: Notificaciones */}
              <div className="flex items-center gap-2">
                <NotificationBell />
              </div>
            </div>
          </header>

          <main className="flex-1 p-4 sm:p-6 lg:p-8">{children}</main>
        </div>
      </div>
    </div>
  );
}