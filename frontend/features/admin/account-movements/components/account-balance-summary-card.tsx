"use client";

import { ArrowDownCircle, ArrowUpCircle, Scale, Users } from "lucide-react";
import { cn } from "@/lib/utils";
import { getAccountEntityLabels } from "@/features/admin/account-movements/components/account-entity-labels";
import { formatCurrency } from "@/features/admin/account-movements/components/account-movement-helpers";
import { useAccountBalanceSummary } from "@/features/admin/account-movements/hooks/use-account-movements-stats";
import type { AccountMovementEntityType } from "@/features/admin/account-movements/types";

type Props = {
  entityType: AccountMovementEntityType;
};

export function AccountBalanceSummaryCard({ entityType }: Props) {
  const { data, isLoading } = useAccountBalanceSummary(entityType);
  const labels = getAccountEntityLabels(entityType);

  const items = [
    {
      title: labels.totalDebtTitle,
      value: data ? formatCurrency(data.total_debt) : "—",
      description: `${data?.debtor_count ?? 0} ${labels.pluralLower} con saldo deudor`,
      icon: ArrowUpCircle,
      accent: "bg-destructive/15 text-destructive",
    },
    {
      title: labels.totalFavorTitle,
      value: data ? formatCurrency(data.total_favor) : "—",
      description: `${data?.favor_count ?? 0} ${labels.pluralLower} con saldo a favor`,
      icon: ArrowDownCircle,
      accent: "bg-brand-muted text-brand",
    },
    {
      title: "Balance neto",
      value: data ? formatCurrency(data.net_balance) : "—",
      description: labels.netBalanceDescription,
      icon: Scale,
      accent:
        data && Number(data.net_balance) > 0
          ? "bg-destructive/15 text-destructive"
          : "bg-brand-muted text-brand",
    },
    {
      title: labels.countTitle,
      value: data ? data.debtor_count + data.favor_count : "—",
      description: "Con saldo distinto de cero.",
      icon: Users,
      accent: "bg-muted text-muted-foreground",
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
            <div className="h-4 w-24 rounded bg-muted" />
            <div className="mt-3 h-7 w-28 rounded bg-muted" />
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