"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, Users, Truck, Wallet } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { AccountMovementsSearchBar } from "@/features/admin/account-movements/components/account-movements-search-bar";
import { AccountMovementsFilters } from "@/features/admin/account-movements/components/account-movements-filters";
import { AccountMovementsStatsCard } from "@/features/admin/account-movements/components/account-movements-stats-card";
import { ClientAccountMovementsTable } from "@/features/admin/account-movements/components/client-account-movements-table";
import { SupplierAccountMovementsTable } from "@/features/admin/account-movements/components/supplier-account-movements-table";
import { useClientAccountMovementsList } from "@/features/admin/account-movements/hooks/use-client-account-movements-list";
import { useSupplierAccountMovementsList } from "@/features/admin/account-movements/hooks/use-supplier-account-movements-list";
import type {
  AccountMovementEntityType,
  AccountMovementSelectedEntity,
  AccountMovementType,
  AccountReferenceType,
  ClientAccountMovement,
  SupplierAccountMovement,
} from "@/features/admin/account-movements/types";

const PAGE_SIZE = 20;

const ENTITY_TABS: {
  value: AccountMovementEntityType;
  label: string;
  icon: typeof Users;
}[] = [
  { value: "client", label: "Clientes", icon: Users },
  { value: "supplier", label: "Proveedores", icon: Truck },
];

export function AccountMovementsList() {
  const [entityType, setEntityType] = useState<AccountMovementEntityType>("client");
  const [page, setPage] = useState(1);
  const [movementType, setMovementType] = useState<AccountMovementType | "all">("all");
  const [referenceType, setReferenceType] = useState<AccountReferenceType | "all">("all");
  const [selectedEntity, setSelectedEntity] =
    useState<AccountMovementSelectedEntity | null>(null);

  const isClient = entityType === "client";

  const clientMovementsQuery = useClientAccountMovementsList({
    page,
    page_size: PAGE_SIZE,
    client_id: selectedEntity?.id ?? null,
    movement_type: movementType,
    reference_type: referenceType,
  });

  const supplierMovementsQuery = useSupplierAccountMovementsList({
    page,
    page_size: PAGE_SIZE,
    supplier_id: selectedEntity?.id ?? null,
    movement_type: movementType,
    reference_type: referenceType,
  });

  const { data, isLoading, isFetching, error } = isClient
    ? clientMovementsQuery
    : supplierMovementsQuery;

  const movements = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = data?.total_pages ?? 1;
  const currentPage = data?.page ?? 1;
  const pageSize = data?.page_size ?? PAGE_SIZE;

  const startItem = total === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, total);

  function handleEntityTypeChange(value: AccountMovementEntityType) {
    setEntityType(value);
    setPage(1);
    setSelectedEntity(null);
  }

  return (
    <div className="space-y-4">
      <div className="inline-flex rounded-xl border bg-background p-1 shadow-sm">
        {ENTITY_TABS.map((tab) => {
          const Icon = tab.icon;
          const active = entityType === tab.value;
          return (
            <Button
              key={tab.value}
              type="button"
              variant="ghost"
              size="sm"
              className={cn(
                "rounded-lg",
                active && "bg-muted text-foreground"
              )}
              onClick={() => handleEntityTypeChange(tab.value)}
            >
              <Icon className="mr-2 h-4 w-4" />
              {tab.label}
            </Button>
          );
        })}
      </div>

      <AccountMovementsSearchBar
        key={entityType}
        entityType={entityType}
        selectedEntity={selectedEntity}
        onEntitySelect={(entity) => {
          setPage(1);
          setSelectedEntity(entity);
        }}
      />

      <AccountMovementsFilters
        movementType={movementType}
        referenceType={referenceType}
        onMovementTypeChange={(value) => {
          setPage(1);
          setMovementType(value);
        }}
        onReferenceTypeChange={(value) => {
          setPage(1);
          setReferenceType(value);
        }}
      />

      <AccountMovementsStatsCard
        entityType={entityType}
        movements={movements}
        total={total}
        selectedEntity={selectedEntity}
        isLoading={isLoading && !data}
      />

      <div className="rounded-2xl border bg-background p-4 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex min-w-0 items-start gap-3">
            <div className="rounded-xl border bg-muted/40 p-2">
              <Wallet className="h-4 w-4" />
            </div>

            <div className="min-w-0 space-y-1">
              <p className="text-sm font-medium">Movimientos de cuenta corriente</p>
              <p className="text-sm text-muted-foreground">
                Mostrando {startItem}-{endItem} de {total} registros.
              </p>
              {isFetching && !isLoading && (
                <p className="text-xs text-muted-foreground">Actualizando datos...</p>
              )}
            </div>
          </div>

          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-end">
            <span className="text-sm text-muted-foreground sm:order-2 sm:min-w-[130px] sm:text-right">
              Página {currentPage} de {totalPages}
            </span>

            <div className="flex gap-2 sm:order-1">
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="flex-1 sm:flex-none"
                onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                disabled={currentPage === 1 || isLoading}
              >
                <ChevronLeft className="mr-1 h-4 w-4" />
                Anterior
              </Button>

              <Button
                type="button"
                variant="outline"
                size="sm"
                className="flex-1 sm:flex-none"
                onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages || isLoading}
              >
                Siguiente
                <ChevronRight className="ml-1 h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {error ? (
        <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          {error instanceof Error
            ? error.message
            : "No se pudieron cargar los movimientos de cuenta corriente."}
        </div>
      ) : isLoading && !data ? (
        <div className="rounded-2xl border bg-background p-6 text-sm text-muted-foreground shadow-sm">
          Cargando movimientos de cuenta corriente...
        </div>
      ) : isClient ? (
        <ClientAccountMovementsTable
          movements={movements as ClientAccountMovement[]}
          showClient={!selectedEntity}
        />
      ) : (
        <SupplierAccountMovementsTable
          movements={movements as SupplierAccountMovement[]}
          showSupplier={!selectedEntity}
        />
      )}
    </div>
  );
}
