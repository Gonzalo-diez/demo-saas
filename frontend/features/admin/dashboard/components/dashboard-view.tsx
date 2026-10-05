"use client";

import { useDashboardSummary } from "@/features/admin/dashboard/hooks/use-dashboard-summary";
import { QuickActions } from "@/features/admin/dashboard/components/quick-actions";
import { StatsCards } from "@/features/admin/dashboard/components/stats-cards";

export function DashboardView() {
  const { data, isLoading, isError } = useDashboardSummary();

  const stats = [
    {
      title: "Productos",
      value: data?.products_total ?? 0,
      description: "Total de productos registrados.",
    },
    {
      title: "Clientes",
      value: data?.clients_total ?? 0,
      description: "Total de clientes cargados.",
    },
    {
      title: "Pedidos",
      value: data?.orders_total ?? 0,
      description: "Total de pedidos registrados.",
    },
    {
      title: "Vendedores",
      value: data?.sales_reps_total ?? 0,
      description: "Total de vendedores activos o creados.",
    },
  ];

  return (
    <div className="space-y-6 p-4">
      <div>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Resumen general del sistema y accesos rápidos.
        </p>
      </div>

      {isError ? (
        <div className="rounded-xl border p-4 text-sm">
          Error al cargar el resumen del dashboard
        </div>
      ) : (
        <StatsCards items={stats} isLoading={isLoading} />
      )}

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Accesos rápidos</h2>
        <QuickActions />
      </div>
    </div>
  );
}