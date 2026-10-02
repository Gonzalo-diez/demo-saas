"use client";

import { Fragment, useMemo, useState } from "react";
import { BarChart3 } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AccountLedgerMetricsPanel } from "@/features/admin/account-ledger/components/account-ledger-metrics-panel";
import { ClientSalesTable } from "@/features/admin/account-ledger/components/client-sales-table";
import { ExportButtons } from "@/features/admin/account-ledger/components/export-buttons";
import { ImportClientSalesCard } from "@/features/admin/account-ledger/components/import-client-sales-card";
import { LedgerDateRangeFilter } from "@/features/admin/account-ledger/components/ledger-date-range-filter";
import { LedgerPagination } from "@/features/admin/account-ledger/components/ledger-pagination";
import { useClientSalesLedger } from "@/features/admin/account-ledger/hooks/use-client-sales-ledger";
import { useClientSalesSummary } from "@/features/admin/account-ledger/hooks/use-client-sales-summary";
import { ledgerDateRangeFilterSchema } from "@/features/admin/account-ledger/schemas/account-ledger-schema";

const PAGE_SIZE = 20;
const ALL_TAB = "todos";
const UNASSIGNED_TAB = "sin-vendedor";

export function ClientSalesLedger() {
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [showImport, setShowImport] = useState(false);
  const [showMetrics, setShowMetrics] = useState(false);
  const [activeTab, setActiveTab] = useState<string>(ALL_TAB);
  const [page, setPage] = useState(1);

  const isDateRangeValid = useMemo(
    () =>
      ledgerDateRangeFilterSchema.safeParse({
        date_from: dateFrom,
        date_to: dateTo,
      }).success,
    [dateFrom, dateTo]
  );

  const { data: summary, isLoading: isSummaryLoading } = useClientSalesSummary({
    date_from: dateFrom || null,
    date_to: dateTo || null,
  });

  const groups = summary?.groups ?? [];

  const salesRepId =
    activeTab === ALL_TAB || activeTab === UNASSIGNED_TAB
      ? null
      : Number(activeTab);
  const unassigned = activeTab === UNASSIGNED_TAB;

  const { data, isLoading, isError } = useClientSalesLedger(
    {
      page,
      page_size: PAGE_SIZE,
      sales_rep_id: salesRepId,
      unassigned,
      date_from: dateFrom || null,
      date_to: dateTo || null,
    },
    { enabled: isDateRangeValid }
  );

  function handleTabChange(value: string) {
    setActiveTab(value);
    setPage(1);
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">
          Remitos de venta a clientes por vendedor: producto, cantidad, stock actual y formas de pago con
          fecha.
        </p>
        <div className="flex flex-wrap items-center gap-2">
          <LedgerDateRangeFilter
            dateFrom={dateFrom}
            dateTo={dateTo}
            onDateFromChange={(value) => {
              setDateFrom(value);
              setPage(1);
            }}
            onDateToChange={(value) => {
              setDateTo(value);
              setPage(1);
            }}
          />
          <ExportButtons
            tab="clients"
            params={{
              sales_rep_id: salesRepId,
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

      {showMetrics && <AccountLedgerMetricsPanel entityType="client" />}

      {showImport && <ImportClientSalesCard />}

      {isSummaryLoading ? (
        <Skeleton className="h-8 w-64" />
      ) : (
        <Tabs value={activeTab} onValueChange={handleTabChange}>
          <TabsList className="flex-wrap h-auto">
            <TabsTrigger value={ALL_TAB}>
              Todos
              <span className="ml-1.5 text-muted-foreground">({summary?.total_all ?? 0})</span>
            </TabsTrigger>
            {groups.map((group) => {
              const value = group.sales_rep ? String(group.sales_rep.id) : UNASSIGNED_TAB;
              return (
                <TabsTrigger key={value} value={value}>
                  {group.sales_rep?.name ?? "Sin vendedor"}
                  <span className="ml-1.5 text-muted-foreground">({group.total})</span>
                </TabsTrigger>
              );
            })}
          </TabsList>

          <TabsContent value={activeTab}>
            {isLoading && !data ? (
              <div className="space-y-2 pt-4">
                <Skeleton className="h-40 w-full" />
              </div>
            ) : isError ? (
              <p className="py-8 text-center text-sm text-destructive">
                No se pudieron cargar las ventas a clientes.
              </p>
            ) : (
              <Fragment key={activeTab}>
                <ClientSalesTable rows={data?.items ?? []} />
                <LedgerPagination
                  page={data?.page ?? page}
                  totalPages={data?.total_pages ?? 1}
                  isLoading={isLoading}
                  onPageChange={setPage}
                />
              </Fragment>
            )}
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}