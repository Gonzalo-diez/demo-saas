"use client";

import { useState } from "react";
import { TrendingDown, TrendingUp } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { formatCurrency } from "@/features/admin/account-movements/components/account-movement-helpers";
import { getAccountEntityLabels } from "@/features/admin/account-movements/components/account-entity-labels";
import { useAccountRanking } from "@/features/admin/account-movements/hooks/use-account-movements-stats";
import type {
  AccountMovementEntityType,
  AccountRankingOrder,
} from "@/features/admin/account-movements/types";

type Props = {
  entityType: AccountMovementEntityType;
};

type AccountRankingItem = {
  id: string | number;
  name: string;
  balance: number | string;
};

export function AccountRankingCard({ entityType }: Props) {
  const [order, setOrder] = useState<AccountRankingOrder>("debtors");
  const { data, isLoading } = useAccountRanking(entityType, order, 5);
  const labels = getAccountEntityLabels(entityType);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle>
          {order === "debtors" ? labels.rankingDebtorsTitle : labels.rankingFavorTitle}
        </CardTitle>

        <div className="inline-flex rounded-lg border bg-muted/40 p-1">
          <Button
            type="button"
            size="sm"
            variant="ghost"
            className={cn("h-7 rounded-md px-2", order === "debtors" && "bg-background shadow-sm")}
            onClick={() => setOrder("debtors")}
          >
            <TrendingUp className="mr-1 h-3.5 w-3.5" />
            Deudores
          </Button>
          <Button
            type="button"
            size="sm"
            variant="ghost"
            className={cn("h-7 rounded-md px-2", order === "favor" && "bg-background shadow-sm")}
            onClick={() => setOrder("favor")}
          >
            <TrendingDown className="mr-1 h-3.5 w-3.5" />
            A favor
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-10 animate-pulse rounded-md bg-muted" />
            ))}
          </div>
        ) : !data || data.length === 0 ? (
          <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
            No hay {labels.pluralLower} con saldo {order === "debtors" ? "deudor" : "a favor"}.
          </div>
        ) : (
          <ul className="divide-y">
            {data.map((item: AccountRankingItem, index: number) => (
              <li
                key={item.id}
                className="flex items-center justify-between gap-3 py-2.5"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-medium text-muted-foreground">
                    {index + 1}
                  </span>
                  <span className="truncate text-sm font-medium">{item.name}</span>
                </div>
                <span
                  className={cn(
                    "shrink-0 text-sm font-semibold tabular-nums",
                    order === "debtors" ? "text-destructive" : "text-brand"
                  )}
                >
                  {formatCurrency(String(item.balance))}
                </span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}