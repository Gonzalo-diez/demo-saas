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

import type { CategorySummaryEntry } from "@/features/admin/analytics/schemas/analytics-schema";

type Props = {
  data: CategorySummaryEntry[];
  isLoading?: boolean;
};

const chartConfig = {
  amount: {
    label: "Monto",
  },
};

function formatCurrency(value: number) {
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 0,
  }).format(value);
}

export function AnalyticsCategoryBreakdownChart({
  data,
  isLoading = false,
}: Props) {
  const chartData = [...data]
    .sort((a, b) => Number(b.amount) - Number(a.amount))
    .slice(0, 10)
    .map((item) => ({
      category: item.category,
      amount: Number(item.amount),
      qty: item.qty,
      uniqueProducts: item.unique_products,
    }));

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Categorías más compradas Online</CardTitle>
        </CardHeader>

        <CardContent>
          <div className="h-[400px] animate-pulse rounded-md bg-muted" />
        </CardContent>
      </Card>
    );
  }

  if (!chartData.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Categorías más compradas Online</CardTitle>
        </CardHeader>

        <CardContent>
          <div className="flex h-[400px] items-center justify-center text-sm text-muted-foreground">
            Sin datos disponibles
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Categorías más compradas Online</CardTitle>
      </CardHeader>

      <CardContent>
        <ChartContainer config={chartConfig} className="h-[400px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{
                left: 20,
                right: 20,
              }}
            >
              <CartesianGrid horizontal={false} />

              <XAxis
                type="number"
                tickFormatter={(value) =>
                  `$${Number(value).toLocaleString("es-AR")}`
                }
              />

              <YAxis type="category" dataKey="category" width={120} />

              <ChartTooltip
                content={
                  <ChartTooltipContent
                    formatter={(value, _, payload) => {
                      const row = payload?.payload;

                      return [
                        formatCurrency(Number(value)),
                        `${row.qty} unidades · ${row.uniqueProducts} productos`,
                      ];
                    }}
                  />
                }
              />

              <Bar dataKey="amount" radius={4} />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}