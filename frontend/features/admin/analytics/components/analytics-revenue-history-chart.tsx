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
  revenue: {
    label: "Revenue",
  },
};

function formatCurrency(value: number) {
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 0,
  }).format(value);
}

export function AnalyticsRevenueHistoryChart({
  data,
  isLoading = false,
}: Props) {
  const chartData = data.map((item) => ({
    date: item.date,
    revenue: Number(item.revenue_generated),
  }));

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Evolución de Ingresos</CardTitle>
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
          <CardTitle>Evolución de Ingresos</CardTitle>
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
        <CardTitle>Evolución de Ingresos</CardTitle>
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

              <YAxis
                tickFormatter={(value) =>
                  `$${Number(value).toLocaleString("es-AR")}`
                }
              />

              <ChartTooltip
                content={
                  <ChartTooltipContent
                    formatter={(value) => formatCurrency(Number(value))}
                  />
                }
              />

              <Line
                type="monotone"
                dataKey="revenue"
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