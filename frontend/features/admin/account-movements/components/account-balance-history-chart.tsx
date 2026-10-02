"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  formatCurrency,
  formatDateTime,
} from "@/features/admin/account-movements/components/account-movement-helpers";
import { useAccountBalanceHistory } from "@/features/admin/account-movements/hooks/use-account-movements-stats";
import type {
  AccountMovementEntityType,
  AccountMovementSelectedEntity,
} from "@/features/admin/account-movements/types";

type Props = {
  entityType: AccountMovementEntityType;
  selectedEntity: AccountMovementSelectedEntity | null;
};

type HistoryPoint = {
  date: string;
  balance: number | string;
};

type ChartDataItem = {
  date: string;
  balance: number;
};

const chartConfig = {
  balance: {
    label: "Saldo",
  },
};

const entityLabels: Record<AccountMovementEntityType, string> = {
  client: "cliente",
  supplier: "proveedor",
};

export function AccountBalanceHistoryChart({
  entityType,
  selectedEntity,
}: Props) {
  const { data, isLoading } = useAccountBalanceHistory(
    entityType,
    selectedEntity?.id ?? null
  );

  const entityLabel = entityLabels[entityType];

  const title = selectedEntity
    ? `Evolución del saldo de ${selectedEntity.name}`
    : "Evolución del saldo";

  if (!selectedEntity) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>

        <CardContent>
          <div className="flex h-[300px] items-center justify-center text-sm text-muted-foreground">
            Elegí un {entityLabel} en el buscador para ver cómo evolucionó
            su saldo.
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>

        <CardContent>
          <div className="h-[300px] animate-pulse rounded-md bg-muted" />
        </CardContent>
      </Card>
    );
  }

  const chartData: ChartDataItem[] = (data ?? []).map((point: HistoryPoint) => ({
    date: formatDateTime(point.date),
    balance: Number(point.balance),
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>

      <CardContent>
        {chartData.length === 0 ? (
          <div className="flex h-[300px] items-center justify-center text-sm text-muted-foreground">
            Todavía no hay movimientos registrados para este {entityLabel}.
          </div>
        ) : (
          <ChartContainer config={chartConfig} className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid vertical={false} />

                <XAxis
                  dataKey="date"
                  tickLine={false}
                  axisLine={false}
                  tickMargin={8}
                  hide
                />

                <YAxis
                  tickFormatter={(value) =>
                    `$${Number(value).toLocaleString("es-AR")}`
                  }
                />

                <ChartTooltip
                  content={
                    <ChartTooltipContent
                      formatter={(value) => formatCurrency(String(value))}
                    />
                  }
                />

                <Line
                  type="monotone"
                  dataKey="balance"
                  stroke="currentColor"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  );
}