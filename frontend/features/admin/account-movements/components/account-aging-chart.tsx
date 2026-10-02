"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
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
import { formatCurrency } from "@/features/admin/account-movements/components/account-movement-helpers";
import { useAccountAgingSummary } from "@/features/admin/account-movements/hooks/use-account-movements-stats";
import type { AccountMovementEntityType } from "@/features/admin/account-movements/types";

type Props = {
  entityType: AccountMovementEntityType;
};

type AccountAgingBucket = {
  label: string;
  amount: number | string;
  invoice_count: number;
};

type ChartDataItem = {
  label: string;
  amount: number;
  invoiceCount: number;
};

const chartConfig = {
  amount: {
    label: "Monto pendiente",
  },
};

export function AccountAgingChart({ entityType }: Props) {
  const { data, isLoading } = useAccountAgingSummary(entityType);
  const isClient = entityType === "client";

  const title = isClient
    ? "Antigüedad de deuda de clientes"
    : "Antigüedad de deuda con proveedores";

  const chartData: ChartDataItem[] =
    data?.buckets.map((bucket: AccountAgingBucket) => ({
      label: bucket.label,
      amount: Number(bucket.amount),
      invoiceCount: bucket.invoice_count,
    })) ?? [];

  const hasData = chartData.some((item) => item.amount > 0);

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

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle>{title}</CardTitle>
        {data && (
          <p className="text-sm text-muted-foreground">
            Total pendiente: {formatCurrency(data.total_pending)}
          </p>
        )}
      </CardHeader>

      <CardContent>
        {!hasData ? (
          <div className="flex h-[300px] items-center justify-center text-sm text-muted-foreground">
            {isClient
              ? "No hay remitos de venta pendientes de cobro."
              : "No hay remitos de compra pendientes de pago."}
          </div>
        ) : (
          <ChartContainer config={chartConfig} className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ left: 8, right: 8 }}>
                <CartesianGrid vertical={false} />

                <XAxis
                  dataKey="label"
                  tickLine={false}
                  axisLine={false}
                  tickMargin={8}
                />

                <YAxis
                  tickFormatter={(value) =>
                    `$${Number(value).toLocaleString("es-AR")}`
                  }
                />

                <ChartTooltip
                  content={
                    <ChartTooltipContent
                      formatter={(value, _, payload) => {
                        const row = payload?.payload;
                        return [
                          formatCurrency(String(value)),
                          `${row.invoiceCount} remito(s) pendiente(s)`,
                        ];
                      }}
                    />
                  }
                />

                <Bar dataKey="amount" radius={4} fill="var(--destructive)" />
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  );
}