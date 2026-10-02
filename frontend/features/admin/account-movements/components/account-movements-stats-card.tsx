"use client";

import { ArrowDownCircle, ArrowUpCircle, ListChecks, Wallet } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatCurrency } from "@/features/admin/account-movements/components/account-movement-helpers";
import type {
  AccountMovementEntityType,
  AccountMovementSelectedEntity,
  ClientAccountMovement,
  SupplierAccountMovement,
} from "@/features/admin/account-movements/types";

type AccountMovementsStatsCardProps = {
  entityType: AccountMovementEntityType;
  movements: (ClientAccountMovement | SupplierAccountMovement)[];
  total: number;
  selectedEntity: AccountMovementSelectedEntity | null;
  isLoading: boolean;
};

// Tipos que aumentan la deuda hacia nosotros (cargos)
const CHARGE_TYPES = new Set(["invoice"]);
// Tipos que la reducen (cobros/pagos, notas de crédito, reversiones)
const CREDIT_TYPES = new Set(["invoice_reversal", "payment", "credit_note"]);

export function AccountMovementsStatsCard({
  entityType,
  movements,
  total,
  selectedEntity,
  isLoading,
}: AccountMovementsStatsCardProps) {
  const charges = movements
    .filter((m) => CHARGE_TYPES.has(m.movement_type))
    .reduce((sum, m) => sum + Number(m.amount), 0);

  const credits = movements
    .filter((m) => CREDIT_TYPES.has(m.movement_type))
    .reduce((sum, m) => sum + Math.abs(Number(m.amount)), 0);

  const balance = selectedEntity ? Number(selectedEntity.current_balance) : null;

  const items = [
    {
      title: "Movimientos",
      value: total,
      description: "Total de registros que coinciden con los filtros.",
      icon: ListChecks,
      accent: "bg-muted text-muted-foreground",
    },
    {
      title: "Cargos (remitos)",
      value: formatCurrency(String(charges)),
      description: "Suma de remitos de esta página.",
      icon: ArrowUpCircle,
      accent: "bg-destructive/15 text-destructive",
    },
    {
      title: "Cobros/Pagos",
      value: formatCurrency(String(credits)),
      description: "Suma de pagos y notas de crédito de esta página.",
      icon: ArrowDownCircle,
      accent: "bg-brand-muted text-brand",
    },
    {
      title: selectedEntity
        ? `Saldo de ${selectedEntity.name}`
        : entityType === "client"
          ? "Saldo del cliente"
          : "Saldo del proveedor",
      value: balance !== null ? formatCurrency(String(balance)) : "—",
      description: selectedEntity
        ? "Saldo actual según el último movimiento registrado."
        : "Elegí un cliente o proveedor en el buscador para ver su saldo.",
      icon: Wallet,
      accent:
        balance !== null && balance > 0
          ? "bg-destructive/15 text-destructive"
          : "bg-brand-muted text-brand",
    },
  ];

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="animate-pulse rounded-2xl border bg-background p-5 shadow-sm"
          >
            <div className="mb-4 h-8 w-8 rounded-lg bg-muted" />
            <div className="h-4 w-20 rounded bg-muted" />
            <div className="mt-3 h-7 w-24 rounded bg-muted" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <div
            key={item.title}
            className="rounded-2xl border bg-background p-5 shadow-sm"
          >
            <div
              className={cn(
                "mb-4 flex h-9 w-9 items-center justify-center rounded-lg",
                item.accent
              )}
            >
              <Icon className="size-4" />
            </div>
            <p className="text-sm text-muted-foreground">{item.title}</p>
            <p className="mt-2 text-2xl font-bold tabular-nums">{item.value}</p>
            <p className="mt-2 text-xs text-muted-foreground">
              {item.description}
            </p>
          </div>
        );
      })}
    </div>
  );
}
