import Link from "next/link";
import { ShoppingBag, LogIn } from "lucide-react";
import { TenantBrand, TenantName } from "@/features/tenant/components/tenant-brand";

export function Footer() {
  return (
    <footer className="border-t bg-card">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
          {/* Empresa */}
          <div>
            <TenantBrand markClassName="h-8 w-8 text-xs" />
            <p className="mt-3 max-w-md text-sm text-muted-foreground">
              Catálogo mayorista online para comercios. Pedidos rápidos y
              entrega directa.
            </p>
          </div>

          {/* Navegación */}
          <div>
            <h4 className="text-sm font-semibold uppercase tracking-wide text-foreground">
              Tu cuenta
            </h4>

            <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
              <li className="flex items-center gap-2">
                <ShoppingBag size={16} />
                <Link href="/catalogo" className="transition-colors hover:text-foreground">
                  Ver catálogo
                </Link>
              </li>
              <li className="flex items-center gap-2">
                <LogIn size={16} />
                <Link href="/ingresar" className="transition-colors hover:text-foreground">
                  Ingresar con mi cuenta
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Divider */}
        <div className="mt-10 border-t pt-6 text-center text-sm text-muted-foreground">
          © {new Date().getFullYear()} <TenantName />. Todos los derechos
          reservados.
        </div>
      </div>
    </footer>
  );
}
