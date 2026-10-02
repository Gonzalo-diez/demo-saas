"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { useSalesRepMap } from "@/features/admin/sales-rep-map/hooks/use-sales-rep-map";
import type { MapFilters as MapFiltersType } from "@/features/admin/sales-rep-map/types";
import { MapFilters } from "@/features/admin/sales-rep-map/components/map-filters";
import { MapSidebar } from "@/features/admin/sales-rep-map/components/map-sidebar";
import { MapSearch } from "@/features/admin/sales-rep-map/components/map-search";

const SalesRepMap = dynamic(
  () => import("./sales-rep-map").then((mod) => mod.SalesRepMap),
  { ssr: false }
);

export function MapView() {
  // Sin filtro geográfico por defecto: el mapa arranca mostrando a
  // todos los vendedores. lat/lng/radius_km se agregan solo si el
  // usuario completa el filtro de zona.
  const [filters, setFilters] = useState<MapFiltersType>({
    isActive: true,
    search: "",
  });

  const [selectedId, setSelectedId] = useState<number | null>(null);

  const { data, isLoading, isError } = useSalesRepMap(filters);

  const salesReps = data?.sales_reps ?? [];

  const isGeoFilterActive =
    filters.lat !== undefined &&
    filters.lng !== undefined &&
    filters.radius_km !== undefined;

  return (
    <div className="space-y-4 p-4">
      <div>
        <h1 className="text-2xl font-semibold">Mapa de vendedores</h1>
        <p className="text-sm text-muted-foreground">
          Visualizá la ubicación y zona de cobertura de todos los
          vendedores. Usá el filtro de zona para acotar por latitud,
          longitud y radio.
        </p>
      </div>

      <MapSearch
        value={filters.search ?? ""}
        onChange={(search) => setFilters((prev) => ({ ...prev, search }))}
        salesReps={salesReps}
        onSelect={setSelectedId}
      />

      <MapFilters filters={filters} onChange={setFilters} />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[320px_1fr]">
        <MapSidebar
          salesReps={salesReps}
          isLoading={isLoading}
          isError={isError}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />

        <div className="rounded-xl border p-2">
          <SalesRepMap
            salesReps={salesReps}
            centerLat={isGeoFilterActive ? filters.lat : undefined}
            centerLng={isGeoFilterActive ? filters.lng : undefined}
            radiusKm={isGeoFilterActive ? filters.radius_km : undefined}
            isLoading={isLoading}
            isError={isError}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </div>
      </div>
    </div>
  );
}
