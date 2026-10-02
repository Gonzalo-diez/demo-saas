"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { useClientsMap } from "@/features/admin/client-map/hooks/use-clients-map";
import { MapFilters as MapFiltersType } from "@/features/admin/client-map/types";
import { MapFilters } from "@/features/admin/client-map/components/map-filters";
import { MapSidebar } from "@/features/admin/client-map/components/map-sidebar";

const ClientsMap = dynamic(
  () => import("./clients-map").then((mod) => mod.ClientsMap),
  { ssr: false }
);

export function MapView() {
  const [filters, setFilters] = useState<MapFiltersType>({
    isActive: true,
    search: "",
  });
  const [selectedBranchId, setSelectedBranchId] = useState<number | null>(null);

  const { data, isLoading, isError } = useClientsMap(filters);

  const clients = data?.clients ?? [];

  return (
    <div className="space-y-4 p-4">
      <div>
        <h1 className="text-2xl font-semibold">Mapa de clientes</h1>
        <p className="text-sm text-muted-foreground">
          Visualiza las sucursales con coordenadas registradas.
        </p>
      </div>

      <MapFilters filters={filters} onChange={setFilters} />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[320px_1fr]">
        <MapSidebar
          clients={clients}
          isLoading={isLoading}
          isError={isError}
          selectedBranchId={selectedBranchId}
          onSelectBranch={setSelectedBranchId}
        />

        <div className="rounded-xl border p-2">
          <ClientsMap
            clients={clients}
            isLoading={isLoading}
            isError={isError}
            selectedBranchId={selectedBranchId}
            onSelectBranch={setSelectedBranchId}
          />
        </div>
      </div>
    </div>
  );
}