"use client";

import type { MapFilters as MapFiltersType } from "@/features/admin/client-map/types";

type MapFiltersProps = {
  filters: MapFiltersType;
  onChange: (filters: MapFiltersType) => void;
};

export function MapFilters({ filters, onChange }: MapFiltersProps) {
  return (
    <div className="grid grid-cols-1 gap-3 rounded-xl border p-4 md:grid-cols-3">
      <input
        type="text"
        placeholder="Buscar cliente o sucursal..."
        value={filters.search ?? ""}
        onChange={(e) =>
          onChange({
            ...filters,
            search: e.target.value,
          })
        }
        className="rounded-md border px-3 py-2 text-sm"
      />

      <select
        value={
          filters.isActive === undefined ? "all" : filters.isActive ? "active" : "inactive"
        }
        onChange={(e) => {
          const value = e.target.value;

          onChange({
            ...filters,
            isActive:
              value === "all" ? undefined : value === "active" ? true : false,
          });
        }}
        className="rounded-md border px-3 py-2 text-sm"
      >
        <option value="all">Todos</option>
        <option value="active">Activos</option>
        <option value="inactive">Inactivos</option>
      </select>

      <input
        type="number"
        placeholder="ID vendedor"
        value={filters.salesRepId ?? ""}
        onChange={(e) =>
          onChange({
            ...filters,
            salesRepId: e.target.value ? Number(e.target.value) : undefined,
          })
        }
        className="rounded-md border px-3 py-2 text-sm"
      />
    </div>
  );
}