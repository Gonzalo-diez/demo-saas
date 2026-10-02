"use client";

import { useState } from "react";
import {
  useProductsDaily,
  useSalesRepsDaily,
  useClientsDaily,
  useCatalogEventsCount,
  useAnalyticsDailyRange,
  useTopClients,
  useTopProducts,
  useRunAggregation,
} from "@/features/admin/analytics/hooks/use-analytics";
import { AnalyticsDailyStatsCards } from "@/features/admin/analytics/components/analytics-daily-stats-cards";
import { AnalyticsSalesRepsTable } from "@/features/admin/analytics/components/analytics-sales-reps-table";
import { AnalyticsProductsTable } from "@/features/admin/analytics/components/analytics-products-table";
import { AnalyticsClientsTable } from "@/features/admin/analytics/components/analytics-clients-table";
import { AnalyticsCatalogEventsStats } from "@/features/admin/analytics/components/analytics-catalog-events-stats";
import { AnalyticsRevenueHistoryChart } from "@/features/admin/analytics/components/analytics-revenue-history-chart";
import { AnalyticsOrdersHistoryChart } from "@/features/admin/analytics/components/analytics-order-history-chart";
import { AnalyticsMarginHistoryChart } from "@/features/admin/analytics/components/analytics-margin-history-chart";
import { AnalyticsCategoryBreakdownChart } from "@/features/admin/analytics/components/analytics-category-breakdown-chart";
import { TopClientsCard } from "@/features/admin/analytics/components/analytics-top-clients-card";
import { TopProductsCard } from "@/features/admin/analytics/components/analytics-top-products-card";

function todayDate(): string {
  return new Date().toISOString().split("T")[0];
}

export function AnalyticsView() {
  const [targetDate, setTargetDate] = useState<string>(todayDate());

  const productsQuery = useProductsDaily(targetDate);
  const salesRepsQuery = useSalesRepsDaily(targetDate);
  const clientsQuery = useClientsDaily(targetDate);
  const analyticsDailyRangeQuery = useAnalyticsDailyRange({
    start_date: `${targetDate}T00:00:00`,
    end_date: `${targetDate}T23:59:59`,
    limit: 10,
  });
  const eventsCountQuery = useCatalogEventsCount({
    start_date: `${targetDate}T00:00:00`,
    end_date: `${targetDate}T23:59:59`,
  });
  const topProductsQuery = useTopProducts({
    start_date: `${targetDate}T00:00:00`,
    end_date: `${targetDate}T23:59:59`,
    limit: 10,
  });

  const topClientsQuery = useTopClients({
    start_date: `${targetDate}T00:00:00`,
    end_date: `${targetDate}T23:59:59`,
    limit: 10,
  });
  const aggregationMutation = useRunAggregation();

  const isLoading =
    productsQuery.isLoading ||
    salesRepsQuery.isLoading ||
    clientsQuery.isLoading ||
    analyticsDailyRangeQuery.isLoading

  // Compute global totals from products/reps data
  const totalRevenue = (salesRepsQuery.data ?? []).reduce(
    (acc, r) => acc + parseFloat(r.revenue_generated),
    0,
  );
  const totalOrders = (salesRepsQuery.data ?? []).reduce(
    (acc, r) => acc + r.total_orders,
    0,
  );
  const totalProductsSold = (salesRepsQuery.data ?? []).reduce(
    (acc, r) => acc + r.total_products_sold,
    0,
  );
  const totalClients = (clientsQuery.data ?? []).length;

  return (
    <div className="space-y-6 p-4">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Analiticas</h1>
          <p className="text-sm text-muted-foreground">
            Métricas diarias de ventas, productos, vendedores y comportamiento
            del catálogo.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 sm:flex-nowrap">
          <input
            type="date"
            value={targetDate}
            max={todayDate()}
            onChange={(e) => setTargetDate(e.target.value)}
            className="min-w-[140px] flex-1 rounded-md border border-input bg-background px-3 py-1.5 text-sm outline-none transition-colors focus:ring-2 focus:ring-ring/50 sm:flex-none"
          />
          <button
            onClick={() => aggregationMutation.mutate(targetDate)}
            disabled={aggregationMutation.isPending}
            className="flex-1 rounded-md border border-input bg-background px-3 py-1.5 text-sm font-medium whitespace-nowrap transition-colors hover:bg-muted disabled:opacity-50 sm:flex-none"
          >
            {aggregationMutation.isPending ? "Procesando..." : "Re-agregar"}
          </button>
        </div>
      </div>

      {aggregationMutation.isSuccess && (
        <div className="rounded-md border border-brand/20 bg-brand/10 px-4 py-2 text-sm font-medium text-brand">
          Agregación completada para {aggregationMutation.data?.target_date}.
        </div>
      )}

      {/* KPI cards */}
      <AnalyticsDailyStatsCards
        isLoading={isLoading}
        totalRevenue={totalRevenue}
        totalOrders={totalOrders}
        totalProductsSold={totalProductsSold}
        totalClients={totalClients}
        catalogEventsCount={eventsCountQuery.data ?? 0}
      />

      {/* Catalog events breakdown */}
      <AnalyticsCatalogEventsStats targetDate={targetDate} />

      {/* Sales reps table */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Por vendedor</h2>
        <AnalyticsSalesRepsTable
          data={salesRepsQuery.data ?? []}
          isLoading={salesRepsQuery.isLoading}
          isError={salesRepsQuery.isError}
        />
      </div>

      {/* Clients table */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Por cliente</h2>
        <p className="text-sm text-muted-foreground">
          Hacé clic en un cliente para ver el detalle de productos y categorías
          compradas.
        </p>
        <AnalyticsClientsTable
          data={clientsQuery.data ?? []}
          isLoading={clientsQuery.isLoading}
          isError={clientsQuery.isError}
        />
      </div>

      {/* Products table */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Por producto</h2>
        <AnalyticsProductsTable
          data={productsQuery.data ?? []}
          isLoading={productsQuery.isLoading}
          isError={productsQuery.isError}
        />
      </div>

      {/* Charts */}
      <div className="space-y-4">
        <div className="grid gap-4 xl:grid-cols-3">
          <AnalyticsRevenueHistoryChart
            data={analyticsDailyRangeQuery.data ?? []}
            isLoading={analyticsDailyRangeQuery.isLoading}
          />

          <AnalyticsOrdersHistoryChart
            data={analyticsDailyRangeQuery.data ?? []}
            isLoading={analyticsDailyRangeQuery.isLoading}
          />

          <AnalyticsMarginHistoryChart
            data={analyticsDailyRangeQuery.data ?? []}
            isLoading={analyticsDailyRangeQuery.isLoading}
          />
        </div>
      </div>

      {/* Cards */}
      <div className="grid gap-4 lg:grid-cols-2">
        <TopProductsCard
          data={topProductsQuery.data ?? []}
          isLoading={topProductsQuery.isLoading}
        />

        <TopClientsCard
          data={topClientsQuery.data ?? []}
          isLoading={topClientsQuery.isLoading}
        />
      </div>
    </div>
  );
}