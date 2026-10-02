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

import type { AnalyticsDaily } from "@/features/admin/analytics/schemas/analytics-schema";

type Props = {
  data: AnalyticsDaily[];
  isLoading?: boolean;
};

const chartConfig = {
  orders: {
    label: "Pedidos",
  },
};

export function AnalyticsOrdersHistoryChart({
  data,
  isLoading = false,
}: Props) {
  const chartData = data.map((item) => ({
    date: item.date,
    orders: item.total_orders,
  }));

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Evolución de Pedidos</CardTitle>
        </CardHeader>

        <CardContent>
          <div className="h-[350px] animate-pulse rounded-md bg-muted" />
        </CardContent>
      </Card>
    );
  }

  if (!chartData.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Evolución de Pedidos</CardTitle>
        </CardHeader>

        <CardContent>
          <div className="flex h-[350px] items-center justify-center text-sm text-muted-foreground">
            Sin datos disponibles
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Evolución de Pedidos</CardTitle>
      </CardHeader>

      <CardContent>
        <ChartContainer config={chartConfig} className="h-[350px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid vertical={false} />

              <XAxis
                dataKey="date"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
              />

              <YAxis allowDecimals={false} />

              <ChartTooltip
                content={
                  <ChartTooltipContent
                    formatter={(value) => [`${value} pedidos`, "Pedidos"]}
                  />
                }
              />

              <Line
                type="monotone"
                dataKey="orders"
                stroke="currentColor"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}