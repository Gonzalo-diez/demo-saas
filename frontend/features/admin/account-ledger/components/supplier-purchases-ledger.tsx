"use client";

import { useMemo, useState } from "react";
import { BarChart3 } from "lucide-react";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AccountLedgerMetricsPanel } from "@/features/admin/account-ledger/components/account-ledger-metrics-panel";
import { ExportButtons } from "@/features/admin/account-ledger/components/export-buttons";
import { ImportSupplierPurchasesCard } from "@/features/admin/account-ledger/components/import-supplier-purchases-card";
import { LedgerDateRangeFilter } from "@/features/admin/account-ledger/components/ledger-date-range-filter";
import { SupplierPurchasesTable } from "@/features/admin/account-ledger/components/supplier-purchases-table";
import { useSupplierPurchasesLedger } from "@/features/admin/account-ledger/hooks/use-supplier-purchases-ledger";
import { ledgerDateRangeFilterSchema } from "@/features/admin/account-ledger/schemas/account-ledger-schema";

export function SupplierPurchasesLedger() {
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [showImport, setShowImport] = useState(false);
  const [showMetrics, setShowMetrics] = useState(false);

  const isDateRangeValid = useMemo(
    () =>
      ledgerDateRangeFilterSchema.safeParse({
        date_from: dateFrom,
        date_to: dateTo,
      }).success,
    [dateFrom, dateTo]
  );

  const { data, isLoading, isError } = useSupplierPurchasesLedger(
    {
      date_from: dateFrom || null,
      date_to: dateTo || null,
    },
    { enabled: isDateRangeValid }
  );

  const groups = data?.groups ?? [];

  const [activeRep, setActiveRep] = useState<string | null>(null);

  const repTabValue = useMemo(() => {
    if (groups.length === 0) return "";
    const exists = groups.some(
      (g) => String(g.sales_rep?.id ?? "sin-vendedor") === activeRep
    );
    return exists ? (activeRep as string) : String(groups[0].sales_rep?.id ?? "sin-vendedor");
  }, [groups, activeRep]);

  const activeGroup = groups.find(
    (g) => String(g.sales_rep?.id ?? "sin-vendedor") === repTabValue
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">
          Una tabla por vendedor, con lo que le compra a sus proveedores: producto, cantidad y
          formas de pago con fecha.
        </p>
        <div className="flex flex-wrap items-center gap-2">
          <LedgerDateRangeFilter
            dateFrom={dateFrom}
            dateTo={dateTo}
            onDateFromChange={setDateFrom}
            onDateToChange={setDateTo}
          />
          <ExportButtons
            tab="suppliers"
            params={{
              sales_rep_id: activeGroup?.sales_rep?.id ?? null,
              date_from: dateFrom || null,
              date_to: dateTo || null,
            }}
          />
          <Button type="button" variant="outline" size="sm" onClick={() => setShowMetrics((v) => !v)}>
            <BarChart3 className="mr-1.5 h-4 w-4" />
            {showMetrics ? "Ocultar métricas" : "Ver métricas"}
          </Button>
          <Button type="button" variant="outline" size="sm" onClick={() => setShowImport((v) => !v)}>
            {showImport ? "Ocultar import" : "Importar Excel"}
          </Button>
        </div>
      </div>

      {showMetrics && <AccountLedgerMetricsPanel entityType="supplier" />}

      {showImport && <ImportSupplierPurchasesCard />}

      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-40 w-full" />
        </div>
      ) : isError ? (
        <p className="py-8 text-center text-sm text-destructive">
          No se pudieron cargar las compras a proveedores.
        </p>
      ) : groups.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">
          No hay vendedores ni compras cargadas todavía.
        </p>
      ) : (
        <Tabs
          value={repTabValue}
          onValueChange={setActiveRep}
        >
          <TabsList className="flex-wrap h-auto">
            {groups.map((group) => {
              const value = String(group.sales_rep?.id ?? "sin-vendedor");
              return (
                <TabsTrigger key={value} value={value}>
                  {group.sales_rep?.name ?? "Sin vendedor"}
                  <span className="ml-1.5 text-muted-foreground">({group.total})</span>
                </TabsTrigger>
              );
            })}
          </TabsList>

          {groups.map((group) => {
            const value = String(group.sales_rep?.id ?? "sin-vendedor");
            return (
              <TabsContent key={value} value={value}>
                <SupplierPurchasesTable rows={group.rows} />
              </TabsContent>
            );
          })}
        </Tabs>
      )}
    </div>
  );
}