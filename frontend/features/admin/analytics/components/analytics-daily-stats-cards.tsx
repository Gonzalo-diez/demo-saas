"use client";

import {
  DollarSign,
  ClipboardList,
  Package,
  Users,
  MousePointerClick,
} from "lucide-react";
import { cn } from "@/lib/utils";

type Props = {
  isLoading: boolean;
  totalRevenue: number;
  totalOrders: number;
  totalProductsSold: number;
  totalClients: number;
  catalogEventsCount: number;
};

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 0,
  }).format(value);
}

export function AnalyticsDailyStatsCards({
  isLoading,
  totalRevenue,
  totalOrders,
  totalProductsSold,
  totalClients,
  catalogEventsCount,
}: Props) {
  const cards = [
    {
      title: "Ingresos del día",
      value: formatCurrency(totalRevenue),
      description: "Suma de todas las remitos de venta.",
      icon: DollarSign,
      accent:
        "bg-brand/10 text-brand",
    },
    {
      title: "Pedidos",
      value: totalOrders,
      description: "Órdenes cerradas en el día.",
      icon: ClipboardList,
      accent: "bg-chart-3/10 text-chart-3",
    },
    {
      title: "Productos vendidos",
      value: totalProductsSold,
      description: "Unidades totales despachadas.",
      icon: Package,
      accent:
        "bg-kraft/10 text-kraft",
    },
    {
      title: "Clientes activos",
      value: totalClients,
      description: "Clientes con al menos una compra.",
      icon: Users,
      accent:
        "bg-chart-4/10 text-chart-4",
    },
    {
      title: "Eventos de catálogo",
      value: catalogEventsCount,
      description: "Vistas, clicks y búsquedas del día.",
      icon: MousePointerClick,
      accent: "bg-destructive/10 text-destructive",
    },
  ];

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="animate-pulse rounded-xl border bg-background p-5"
          >
            <div className="mb-4 h-8 w-8 rounded-lg bg-muted" />
            <div className="h-4 w-24 rounded bg-muted" />
            <div className="mt-3 h-8 w-16 rounded bg-muted" />
            <div className="mt-3 h-3 w-28 rounded bg-muted" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div key={card.title} className="rounded-xl border bg-background p-5">
            <div
              className={cn(
                "mb-4 flex h-9 w-9 items-center justify-center rounded-lg",
                card.accent,
              )}
            >
              <Icon className="size-4" />
            </div>
            <p className="text-sm text-muted-foreground">{card.title}</p>
            <p className="mt-2 text-2xl font-bold tabular-nums">{card.value}</p>
            <p className="mt-2 text-xs text-muted-foreground">
              {card.description}
            </p>
          </div>
        );
      })}
    </div>
  );
}