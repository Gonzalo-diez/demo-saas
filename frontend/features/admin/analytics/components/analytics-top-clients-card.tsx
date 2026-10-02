"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import type { AnalyticsClientDaily } from "@/features/admin/analytics/schemas/analytics-schema";

type Props = {
  data: AnalyticsClientDaily[];
  isLoading?: boolean;
};

function formatCurrency(value: string | number) {
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 0,
  }).format(Number(value));
}

export function TopClientsCard({ data, isLoading = false }: Props) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Top Clientes</CardTitle>
        </CardHeader>

        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, index) => (
              <div
                key={index}
                className="h-10 animate-pulse rounded-md bg-muted"
              />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const clients = [...data]
    .sort((a, b) => Number(b.revenue_generated) - Number(a.revenue_generated))
    .slice(0, 10);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Top Clientes</CardTitle>
      </CardHeader>

      <CardContent>
        {clients.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            Sin datos disponibles
          </div>
        ) : (
          <div className="space-y-3">
            {clients.map((client, index) => (
              <div
                key={`${client.client_id}-${index}`}
                className="flex items-center justify-between"
              >
                <div>
                  <div className="font-medium">#{client.client_id}</div>

                  <div className="text-xs text-muted-foreground">
                    {client.total_orders} pedidos
                  </div>
                </div>

                <div className="text-right">
                  <div className="font-medium">
                    {formatCurrency(client.revenue_generated)}
                  </div>

                  <div className="text-xs text-muted-foreground">
                    {client.unique_products_count} productos
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}