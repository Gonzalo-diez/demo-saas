import { Truck, Package, Clock } from "lucide-react";

// Ancho de cada barra del "código de barras" decorativo — fijo para evitar
// mismatches de hidratación (nada de Math.random en render).
const BARCODE_WIDTHS = [2, 1, 3, 1, 2, 4, 1, 2, 1, 3, 2, 1, 4, 1, 2, 3, 1, 2, 1, 3];

export function HeroCarousel() {
  return (
    <section className="relative overflow-hidden border-b bg-foreground text-background">
      {/* Textura de fondo: grilla de puntos, muy sutil */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            "radial-gradient(circle at 1px 1px, var(--background) 1px, transparent 0)",
          backgroundSize: "28px 28px",
          opacity: 0.05,
        }}
      />

      <div className="relative mx-auto max-w-7xl px-4 py-14 sm:px-6 sm:py-20 lg:py-24">
        <div className="grid gap-10 lg:grid-cols-[1fr_320px] lg:items-center lg:gap-16">
          {/* Copy principal */}
          <div className="max-w-xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-background/15 bg-background/5 px-3 py-1">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[var(--brand)] opacity-75" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-[var(--brand)]" />
              </span>
              <span className="font-mono text-[11px] font-medium uppercase tracking-widest text-background/80">
                Distribuidora mayorista · Pedidos abiertos
              </span>
            </div>

            <h1 className="font-heading text-4xl font-black leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl">
              Pedidos rápidos.
              <br />
              <span className="text-[var(--brand)]">Entrega directa.</span>
            </h1>

            <p className="mt-6 max-w-md text-base text-background/70 sm:text-lg">
              Cigarrillos, tabaco, accesorios y productos de farmacia al por
              mayor. Hacé tu pedido en minutos y lo recibís en tu local.
            </p>
          </div>

          {/* Hoja de ruta / remito — elemento distintivo */}
          <div className="relative mx-auto w-full max-w-xs lg:mx-0">
            <div className="rounded-2xl border border-background/10 bg-background/[0.06] p-5 backdrop-blur-sm">
              <div className="flex items-center justify-between border-b border-dashed border-background/20 pb-3">
                <span className="font-mono text-[11px] uppercase tracking-widest text-background/50">
                  Hoja de ruta
                </span>
                <span className="font-mono text-[11px] text-background/50">
                  #DC-001
                </span>
              </div>

              <dl className="mt-4 space-y-4">
                {[
                  { icon: Package, label: "Stock", value: "Amplio catálogo" },
                  { icon: Truck, label: "Zona", value: "Mercedes y alrededores" },
                  { icon: Clock, label: "Horario", value: "Lun–Vie · 8 a 18 h" },
                ].map(({ icon: Icon, label, value }) => (
                  <div key={label} className="flex items-start gap-3">
                    <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-[var(--brand)]/15">
                      <Icon className="h-4 w-4 text-[var(--brand)]" />
                    </div>
                    <div>
                      <dt className="font-mono text-[10px] uppercase tracking-widest text-background/45">
                        {label}
                      </dt>
                      <dd className="text-sm font-medium text-background/90">
                        {value}
                      </dd>
                    </div>
                  </div>
                ))}
              </dl>

              {/* Código de barras decorativo */}
              <div
                aria-hidden
                className="mt-5 flex h-6 items-end gap-[2px] border-t border-dashed border-background/20 pt-3"
              >
                {BARCODE_WIDTHS.map((w, i) => (
                  <span
                    key={i}
                    className="h-full bg-background/25"
                    style={{ width: `${w * 2}px` }}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}