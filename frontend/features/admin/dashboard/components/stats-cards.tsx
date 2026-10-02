"use client";

import type { LucideIcon } from "lucide-react";
import { Package, Users, ClipboardList, UserCheck } from "lucide-react";
import { cn } from "@/lib/utils";

export type StatCardItem = {
  title: string;
  value: number | string;
  description: string;
  icon?: LucideIcon;
  trend?: string;
};

const DEFAULT_ICONS: Record<string, LucideIcon> = {
  Productos: Package,
  Clientes: Users,
  Pedidos: ClipboardList,
  Vendedores: UserCheck,
};

type StatsCardsProps = {
  items: StatCardItem[];
  isLoading: boolean;
};

export function StatsCards({ items, isLoading }: StatsCardsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="animate-pulse rounded-xl border bg-background p-5"
          >
            <div className="mb-4 h-8 w-8 rounded-lg bg-muted" />
            <div className="h-4 w-20 rounded bg-muted" />
            <div className="mt-3 h-8 w-14 rounded bg-muted" />
            <div className="mt-3 h-3 w-28 rounded bg-muted" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
      {items.map((item, i) => {
        const Icon = item.icon ?? DEFAULT_ICONS[item.title];
        const accent = [
          "bg-[var(--brand-muted)] text-[var(--brand)]",
          "bg-[var(--kraft)]/15 text-[var(--kraft)]",
          "bg-[var(--chart-3)]/15 text-[var(--chart-3)]",
          "bg-muted text-muted-foreground",
        ][i % 4];

        return (
          <div key={item.title} className="rounded-xl border bg-background p-5">
            {Icon && (
              <div
                className={cn(
                  "mb-4 flex h-9 w-9 items-center justify-center rounded-lg",
                  accent,
                )}
              >
                <Icon className="size-4" />
              </div>
            )}
            <p className="text-sm text-muted-foreground">{item.title}</p>
            <p className="mt-2 text-3xl font-bold tabular-nums">{item.value}</p>
            {item.trend ? (
              <p className="mt-2 text-xs font-medium text-[var(--brand)]">
                {item.trend}
              </p>
            ) : (
              <p className="mt-2 text-xs text-muted-foreground">
                {item.description}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}