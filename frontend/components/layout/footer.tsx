import Link from "next/link";
import { Phone, Mail, MapPin, Clock } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t bg-background">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
          {/* Empresa */}
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--brand)] text-[var(--brand-foreground)] text-xs font-bold">
                DC
              </span>
              <h3 className="text-base font-semibold">Distri Choco</h3>
            </div>
            <p className="mt-3 text-sm text-muted-foreground">
              Distribuidora mayorista de cigarrillos, tabaco, accesorios y
              productos de farmacia. Pedidos rápidos y entrega directa.
            </p>
          </div>

          {/* Navegación */}
          <div>
            <h4 className="text-sm font-semibold uppercase tracking-wide text-foreground">
              Catálogo
            </h4>

            <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
              <li>
                <Link
                  href="/catalogo/analgesicos-farmacia"
                  className="hover:text-foreground transition-colors"
                >
                  Analgésicos
                </Link>
              </li>

              <li>
                <Link
                  href="/catalogo/cigarrillos-economicos"
                  className="hover:text-foreground transition-colors"
                >
                  Cigarrillos Económicos
                </Link>
              </li>

              <li>
                <Link
                  href="/catalogo/cigarrillos-massalin-bat"
                  className="hover:text-foreground transition-colors"
                >
                  Cigarrillos Massalin / BAT
                </Link>
              </li>

              <li>
                <Link
                  href="/catalogo/tabaco-accesorios"
                  className="hover:text-foreground transition-colors"
                >
                  Tabaco y Accesorios
                </Link>
              </li>
            </ul>
          </div>

          {/* Contacto */}
          <div>
            <h4 className="text-sm font-semibold uppercase tracking-wide text-foreground">
              Contacto
            </h4>

            <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
              <li className="flex items-center gap-2">
                <Phone size={16} />
                <a
                  href="https://wa.me/549XXXXXXXXX"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-foreground transition-colors"
                >
                  WhatsApp
                </a>
              </li>

              <li className="flex items-center gap-2">
                <Mail size={16} />
                ventas@districhoco.com
              </li>

              <li className="flex items-center gap-2">
                <MapPin size={16} />
                Mercedes, Provincia Buenos Aires, Argentina
              </li>

              <li className="flex items-center gap-2">
                <MapPin size={16} />
                Zona de reparto: Mercedes y alrededores
              </li>

              <li className="flex items-center gap-2">
                <Clock size={16} />
                Lunes a Viernes, 8:00 a 18:00
              </li>
            </ul>
          </div>
        </div>

        {/* Divider */}
        <div className="mt-10 border-t pt-6 text-center text-sm text-muted-foreground">
          © {new Date().getFullYear()} Distri Choco. Todos los derechos
          reservados.
        </div>
      </div>
    </footer>
  );
}