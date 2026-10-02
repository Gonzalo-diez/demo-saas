"use client";

import Link from "next/link";
import { NAV_ITEMS } from "@/constants/navigation";

// Excluimos dashboard porque ya estamos en él
const QUICK_ACTION_HREFS = [
  "/admin/products",
  "/admin/inventory-movements",
  "/admin/clients",
  "/admin/orders",
  "/admin/sales",
  "/admin/purchases",
  "/admin/sales-invoices",
  "/admin/purchase-invoices",
  "/admin/suppliers",
  "/admin/sales-reps",
  "/admin/client-map",
  "/admin/sales-rep-map",
  "/admin/analytics",
];

const DESCRIPTIONS: Record<string, string> = {
  "/admin/products": "Catálogo y stock",
  "/admin/inventory-movements": "Movimientos de inventario",
  "/admin/clients": "Base de clientes",
  "/admin/orders": "Estado y seguimiento",
  "/admin/sales": "Remitos y presupuestos de venta",
  "/admin/purchases": "Remitos y presupuestos de compra",
  "/admin/sales-invoices": "Remitos de venta",
  "/admin/purchase-invoices": "Facturación de compras",
  "/admin/suppliers": "Gestión de proveedores",
  "/admin/sales-reps": "Equipo comercial",
  "/admin/client-map": "Clientes en el mapa",
  "/admin/sales-rep-map": "Vendedores en el mapa",
  "/admin/analytics": "Métricas y reportes",
};

export function QuickActions() {
  const actions = NAV_ITEMS.filter((item) =>
    QUICK_ACTION_HREFS.includes(item.href),
  );

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4">
      {actions.map((action) => {
        const Icon = action.icon;
        return (
          <Link
            key={action.href}
            href={action.href}
            className="group flex items-start gap-3 rounded-xl border bg-background p-4 transition-all hover:-translate-y-0.5 hover:shadow-sm hover:bg-muted/30"
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted transition-colors group-hover:bg-background">
              <Icon className="size-4 text-muted-foreground" />
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{action.label}</p>
              <p className="mt-0.5 truncate text-xs text-muted-foreground">
                {DESCRIPTIONS[action.href]}
              </p>
            </div>
          </Link>
        );
      })}
    </div>
  );
}