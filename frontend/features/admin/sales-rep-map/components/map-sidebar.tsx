"use client";

import type { MapSalesRep } from "@/features/admin/sales-rep-map/types";

type MapSidebarProps = {
  salesReps: MapSalesRep[];
  isLoading: boolean;
  isError: boolean;
  selectedId: number | null;
  onSelect: (id: number) => void;
};

export function MapSidebar({
  salesReps,
  isLoading,
  isError,
  selectedId,
  onSelect,
}: MapSidebarProps) {
  if (isLoading) {
    return (
      <div className="flex h-[600px] items-center justify-center rounded-xl border p-4 text-sm text-muted-foreground">
        Cargando vendedores...
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex h-[600px] items-center justify-center rounded-xl border p-4 text-sm text-destructive">
        Error al cargar vendedores
      </div>
    );
  }

  if (salesReps.length === 0) {
    return (
      <div className="flex h-[600px] items-center justify-center rounded-xl border p-4 text-sm text-muted-foreground">
        No hay vendedores que coincidan con los filtros
      </div>
    );
  }

  return (
    <div className="h-[600px] overflow-y-auto rounded-xl border p-2">
      <p className="mb-2 px-2 text-xs font-medium text-muted-foreground">
        {salesReps.length} vendedor{salesReps.length !== 1 ? "es" : ""}
      </p>

      <div className="space-y-2">
        {salesReps.map((rep) => {
          const isSelected = selectedId === rep.id;

          return (
            <button
              key={rep.id}
              type="button"
              onClick={() => onSelect(rep.id)}
              className={`w-full rounded-lg border p-3 text-left transition ${
                isSelected
                  ? "border-primary bg-muted"
                  : "hover:bg-muted/50"
              }`}
            >
              <p className="font-medium text-sm">{rep.name}</p>

              {rep.coverage_radius_km != null && (
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Cobertura: {rep.coverage_radius_km} km
                </p>
              )}

              {rep.home_lat != null && rep.home_lng != null ? (
                <p className="text-xs text-muted-foreground">
                  {rep.home_lat.toFixed(4)}, {rep.home_lng.toFixed(4)}
                </p>
              ) : (
                <p className="text-xs text-muted-foreground italic">
                  Sin coordenadas
                </p>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
