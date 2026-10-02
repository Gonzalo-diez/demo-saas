"use client";

import type { MapFilters as MapFiltersType } from "@/features/admin/sales-rep-map/types";

type MapFiltersProps = {
  filters: MapFiltersType;
  onChange: (filters: MapFiltersType) => void;
};

function toOptionalNumber(raw: string): number | undefined {
  if (raw === "") return undefined;
  const parsed = Number(raw);
  return Number.isNaN(parsed) ? undefined : parsed;
}

export function MapFilters({ filters, onChange }: MapFiltersProps) {
  const hasAnyGeoField =
    filters.lat !== undefined ||
    filters.lng !== undefined ||
    filters.radius_km !== undefined;

  const isGeoIncomplete =
    hasAnyGeoField &&
    (filters.lat === undefined ||
      filters.lng === undefined ||
      filters.radius_km === undefined);

  return (
    <div className="space-y-3 rounded-xl border p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs font-medium text-muted-foreground">
          Filtro por zona (opcional): acota los vendedores a un radio
          alrededor de un punto. Sin esto, el mapa muestra a todos.
        </p>

        {hasAnyGeoField && (
          <button
            type="button"
            onClick={() =>
              onChange({
                ...filters,
                lat: undefined,
                lng: undefined,
                radius_km: undefined,
              })
            }
            className="text-xs font-medium text-primary hover:underline"
          >
            Limpiar filtro de zona
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-muted-foreground">
            Latitud central
          </label>
          <input
            type="number"
            step="any"
            placeholder="-27.36"
            value={filters.lat ?? ""}
            onChange={(e) =>
              onChange({ ...filters, lat: toOptionalNumber(e.target.value) })
            }
            className="rounded-md border px-3 py-2 text-sm"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-muted-foreground">
            Longitud central
          </label>
          <input
            type="number"
            step="any"
            placeholder="-55.90"
            value={filters.lng ?? ""}
            onChange={(e) =>
              onChange({ ...filters, lng: toOptionalNumber(e.target.value) })
            }
            className="rounded-md border px-3 py-2 text-sm"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-muted-foreground">
            Radio (km)
          </label>
          <input
            type="number"
            min={1}
            step={1}
            placeholder="50"
            value={filters.radius_km ?? ""}
            onChange={(e) =>
              onChange({
                ...filters,
                radius_km: toOptionalNumber(e.target.value),
              })
            }
            className="rounded-md border px-3 py-2 text-sm"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-muted-foreground">
            Estado
          </label>
          <select
            value={
              filters.isActive === undefined
                ? "all"
                : filters.isActive
                ? "active"
                : "inactive"
            }
            onChange={(e) => {
              const value = e.target.value;
              onChange({
                ...filters,
                isActive:
                  value === "all"
                    ? undefined
                    : value === "active"
                    ? true
                    : false,
              });
            }}
            className="rounded-md border px-3 py-2 text-sm"
          >
            <option value="all">Todos</option>
            <option value="active">Activos</option>
            <option value="inactive">Inactivos</option>
          </select>
        </div>
      </div>

      {isGeoIncomplete && (
        <p className="text-xs text-amber-600">
          Completá latitud, longitud y radio para aplicar el filtro de zona
          (o limpiá los tres para ver a todos los vendedores).
        </p>
      )}
    </div>
  );
}
