"use client";

import { useEffect, useRef, useState, Fragment } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import {
  ShoppingCart,
  ChevronDown,
  Menu,
  X,
  User,
  LogOut,
  LogIn,
} from "lucide-react";
import { useMounted } from "@/hooks/use-mounted";
import { useCartStore } from "@/store/cart-store";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useClientAuthStore } from "@/features/shop/auth/store/auth-store";
import { useClientLogout } from "@/features/shop/auth/hooks/use-auth";
import { useClientSession } from "@/features/shop/auth/hooks/use-session";
import { useShopCategories } from "@/features/shop/categories/hooks/use-shop-categories";
import { TenantBrand } from "@/features/tenant/components/tenant-brand";

export function Navbar() {
  const totalItems = useCartStore((state) => state.getTotalItems());
  const mounted = useMounted();
  const pathname = usePathname();

  const client = useClientAuthStore((state) => state.client);
  const logout = useClientLogout();

  // El catálogo es público: la sesión (si la hay) se consulta acá para que el
  // menú muestre el nombre del cliente en cualquier página de la tienda.
  useClientSession();

  // Las categorías son de cada distribuidora (las que publicó en su catálogo).
  const { data: categoriesData } = useShopCategories();
  const categories = categoriesData?.items ?? [];

  const hasItems = mounted && totalItems > 0;
  const isAuthenticated = mounted && !!client;

  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const dropdownRef = useRef<HTMLDivElement>(null);

  const catalogoActive = pathname.startsWith("/catalogo");
  const ingresarActive = pathname.startsWith("/ingresar");

  // Cerrar todo al cambiar de página. Ajustamos el estado durante el render (en vez de
  // en un efecto) para evitar un render en cascada:
  // https://react.dev/learn/you-might-not-need-an-effect
  const [prevPathname, setPrevPathname] = useState(pathname);
  if (pathname !== prevPathname) {
    setPrevPathname(pathname);
    setDropdownOpen(false);
    setSidebarOpen(false);
  }

  // Dropdown desktop: cerrar por click afuera / Escape.
  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node)
      ) {
        setDropdownOpen(false);
      }
    }

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setDropdownOpen(false);
        setSidebarOpen(false);
      }
    }

    document.addEventListener("mousedown", onClickOutside);
    document.addEventListener("keydown", onKeyDown);

    return () => {
      document.removeEventListener("mousedown", onClickOutside);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, []);

  // Bloquear scroll del body mientras el sidebar está abierto.
  useEffect(() => {
    document.body.style.overflow = sidebarOpen ? "hidden" : "";

    return () => {
      document.body.style.overflow = "";
    };
  }, [sidebarOpen]);

  return (
    <Fragment>
      <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          {/* Hamburguesa — solo mobile */}
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            aria-label="Abrir menú"
            className="-ml-1.5 flex h-9 w-9 items-center justify-center rounded-md text-foreground hover:bg-muted sm:hidden"
          >
            <Menu className="h-5 w-5" />
          </button>

          {/* Logo */}
          <Link href="/" className="group flex items-center transition-opacity hover:opacity-90">
            <TenantBrand markClassName="h-8 w-8 text-xs" />
          </Link>

          {/* Navegación desktop: el catálogo es público */}
          <nav className="hidden items-center sm:flex">
            {(
              <div ref={dropdownRef} className="relative">
                <button
                  type="button"
                  onClick={() => setDropdownOpen((value) => !value)}
                  aria-expanded={dropdownOpen}
                  aria-haspopup="true"
                  className={cn(
                    "flex items-center gap-1 rounded-md px-2 py-1.5 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand)]/50",
                    catalogoActive
                      ? "font-medium text-foreground"
                      : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  Catálogo
                  <ChevronDown
                    className={cn(
                      "h-3.5 w-3.5 transition-transform",
                      dropdownOpen && "rotate-180",
                    )}
                  />
                </button>

                {dropdownOpen && (
                  <div
                    role="menu"
                    className="absolute left-0 top-full mt-2 w-64 rounded-lg border bg-background p-1.5 shadow-lg"
                  >
                    <Link
                      href="/catalogo"
                      role="menuitem"
                      className="block rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-muted"
                    >
                      Ver todo el catálogo
                    </Link>

                    <div className="my-1 border-t" />

                    {categories.map((cat) => (
                      <Link
                        key={cat.id}
                        href={`/catalogo/${cat.slug}`}
                        role="menuitem"
                        className="block rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
                      >
                        {cat.name}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            )}
          </nav>

          {/* Sesión del cliente */}
          {isAuthenticated && client && (
            <div className="hidden items-center gap-1.5 text-sm text-muted-foreground sm:flex">
              <User className="h-4 w-4" />

              <span className="max-w-[140px] truncate">{client.name}</span>

              <button
                type="button"
                onClick={() => logout.mutate()}
                disabled={logout.isPending}
                aria-label="Cerrar sesión"
                title="Cerrar sesión"
                className="ml-1 flex h-8 w-8 items-center justify-center rounded-md hover:bg-muted hover:text-foreground disabled:pointer-events-none disabled:opacity-50"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          )}

          {/* Carrito: lo ve cualquier visitante (la cuenta se pide al finalizar) */}
          {(
            <Link
              href="/checkout"
              className={cn(
                "flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-colors",
                hasItems
                  ? "border-[var(--brand)]/30 bg-[var(--brand)]/10 hover:bg-[var(--brand)]/15"
                  : "bg-background hover:bg-muted",
              )}
            >
              <ShoppingCart className="h-4 w-4" />

              <span className="hidden sm:inline">Carrito</span>

              {hasItems && (
                <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-[var(--brand)] px-1.5 text-xs font-semibold text-[var(--brand-foreground)]">
                  {totalItems}
                </span>
              )}
            </Link>
          )}

          {/* Botón de ingreso visible en desktop cuando no hay sesión */}
          {!isAuthenticated && (
            <Link
              href="/ingresar"
              className={cn(
                "hidden items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-colors sm:flex",
                ingresarActive
                  ? "border-[var(--brand)]/30 bg-[var(--brand)]/10"
                  : "bg-background hover:bg-muted",
              )}
            >
              <LogIn className="h-4 w-4" />
              Ingresar
            </Link>
          )}
        </div>
      </header>

      {/* Sidebar mobile */}
      {mounted &&
        sidebarOpen &&
        createPortal(
          <div className="fixed inset-0 z-50 sm:hidden">
            {/* Overlay */}
            <div
              className="absolute inset-0 bg-black/40"
              onClick={() => setSidebarOpen(false)}
              aria-hidden
            />

            {/* Panel */}
            <div className="absolute inset-y-0 left-0 flex w-[80%] max-w-xs flex-col bg-background shadow-xl">
              {/* Header del sidebar */}
              <div className="flex items-center justify-between border-b px-4 py-3">
                <span className="text-sm font-semibold tracking-tight">
                  Menú
                </span>

                <button
                  type="button"
                  onClick={() => setSidebarOpen(false)}
                  aria-label="Cerrar menú"
                  className="flex h-8 w-8 items-center justify-center rounded-md hover:bg-muted"
                >
                  <X className="h-4.5 w-4.5" />
                </button>
              </div>

              <nav className="flex-1 overflow-y-auto px-2 py-2">
                {/* Cliente autenticado */}
                {isAuthenticated && client && (
                  <div className="mb-2 flex items-center justify-between rounded-md border px-3 py-2.5">
                    <div className="flex items-center gap-2 overflow-hidden text-sm">
                      <User className="h-4 w-4 shrink-0 text-muted-foreground" />

                      <span className="truncate font-medium">
                        {client.name}
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={() => logout.mutate()}
                      disabled={logout.isPending}
                      aria-label="Cerrar sesión"
                      className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground disabled:pointer-events-none disabled:opacity-50"
                    >
                      <LogOut className="h-4 w-4" />
                    </button>
                  </div>
                )}

                {/* Visitante */}
                {!isAuthenticated && (
                  <Link
                    href="/ingresar"
                    className={cn(
                      "flex items-center gap-2 rounded-md px-3 py-2.5 text-sm font-medium hover:bg-muted",
                      ingresarActive
                        ? "text-foreground"
                        : "text-muted-foreground",
                    )}
                  >
                    <LogIn className="h-4 w-4" />
                    Ingresar
                  </Link>
                )}

                {/* Navegación de la tienda (pública) */}
                {(
                  <Fragment>
                    <Link
                      href="/catalogo"
                      className="block rounded-md px-3 py-2.5 text-sm font-medium text-foreground hover:bg-muted"
                    >
                      Ver todo el catálogo
                    </Link>

                    <p className="mt-3 px-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                      Categorías
                    </p>

                    <div className="mt-1 space-y-0.5">
                      {categories.map((cat) => (
                        <Link
                          key={cat.id}
                          href={`/catalogo/${cat.slug}`}
                          className="block rounded-md px-3 py-2.5 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
                        >
                          {cat.name}
                        </Link>
                      ))}
                    </div>

                    <div className="my-3 border-t" />

                    <Link
                      href="/checkout"
                      className="flex items-center gap-2 rounded-md px-3 py-2.5 text-sm font-medium text-foreground hover:bg-muted"
                    >
                      <ShoppingCart className="h-4 w-4" />
                      Carrito
                      {hasItems && (
                        <span className="ml-auto flex h-5 min-w-5 items-center justify-center rounded-full bg-[var(--brand)] px-1.5 text-xs font-semibold text-[var(--brand-foreground)]">
                          {totalItems}
                        </span>
                      )}
                    </Link>
                  </Fragment>
                )}
              </nav>
            </div>
          </div>,
          document.body,
        )}
    </Fragment>
  );
}