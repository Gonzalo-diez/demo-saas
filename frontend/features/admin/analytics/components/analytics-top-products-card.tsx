"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import type { AnalyticsProductDaily } from "@/features/admin/analytics/schemas/analytics-schema";

type Props = {
  data: AnalyticsProductDaily[];
  isLoading?: boolean;
};

function formatCurrency(value: string | number) {
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 0,
  }).format(Number(value));
}

export function TopProductsCard({ data, isLoading = false }: Props) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Top Productos</CardTitle>
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

  const products = [...data]
    .sort((a, b) => Number(b.revenue_generated) - Number(a.revenue_generated))
    .slice(0, 10);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Top Productos</CardTitle>
      </CardHeader>

      <CardContent>
        {products.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            Sin datos disponibles
          </div>
        ) : (
          <div className="space-y-3">
            {products.map((product, index) => (
              <div
                key={`${product.product_id}-${index}`}
                className="flex items-center justify-between"
              >
                <div>
                  <div className="font-medium">#{product.product_id}</div>

                  <div className="text-xs text-muted-foreground">
                    {product.quantity_sold} unidades
                  </div>
                </div>

                <div className="text-right">
                  <div className="font-medium">
                    {formatCurrency(product.revenue_generated)}
                  </div>

                  <div className="text-xs text-muted-foreground">
                    Margen {formatCurrency(product.margin_generated)}
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