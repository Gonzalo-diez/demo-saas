"use client";

import { useState } from "react";

import { AccountBalanceSummaryCard } from "@/features/admin/account-movements/components/account-balance-summary-card";
import { AccountAgingChart } from "@/features/admin/account-movements/components/account-aging-chart";
import { AccountRankingCard } from "@/features/admin/account-movements/components/account-ranking-card";
import { AccountBalanceHistoryChart } from "@/features/admin/account-movements/components/account-balance-history-chart";
import { AccountEntitySelect } from "@/features/admin/account-ledger/components/account-entity-select";
import type {
  AccountMovementEntityType,
  AccountMovementSelectedEntity,
} from "@/features/admin/account-movements/types";

type Props = {
  entityType: AccountMovementEntityType;
};

const entityLabels: Record<
  AccountMovementEntityType,
  {
    singular: string;
    title: string;
  }
> = {
  client: {
    singular: "cliente",
    title: "Ver evolución de un cliente",
  },
  supplier: {
    singular: "proveedor",
    title: "Ver evolución de un proveedor",
  },
};

/**
 * Métricas de cuenta corriente para clientes y proveedores.
 */
export function AccountLedgerMetricsPanel({ entityType }: Props) {
  const [selectedEntity, setSelectedEntity] =
    useState<AccountMovementSelectedEntity | null>(null);

  const labels = entityLabels[entityType];

  return (
    <div className="space-y-4">
      <AccountBalanceSummaryCard entityType={entityType} />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <AccountAgingChart entityType={entityType} />
        <AccountRankingCard entityType={entityType} />
      </div>

      <div className="space-y-3">
        <div>
          <p className="text-sm font-medium">{labels.title}</p>

          <p className="text-xs text-muted-foreground">
            Elegí un {labels.singular} para ver cómo evolucionó su saldo en
            el tiempo.
          </p>
        </div>

        <AccountEntitySelect
          entityType={entityType}
          selectedEntity={selectedEntity}
          onEntitySelect={setSelectedEntity}
        />

        <AccountBalanceHistoryChart
          entityType={entityType}
          selectedEntity={selectedEntity}
        />
      </div>
    </div>
  );
}