"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { MapSalesRep } from "@/features/admin/sales-rep-map/types";

type MapSearchProps = {
  value: string;
  onChange: (value: string) => void;
  salesReps: MapSalesRep[];
  onSelect: (id: number) => void;
};

export function MapSearch({
  value,
  onChange,
  salesReps,
  onSelect,
}: MapSearchProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const suggestions = useMemo(() => {
    const term = value.trim().toLowerCase();

    if (!term) return [];

    return salesReps
      .filter((rep) => rep.name.toLowerCase().includes(term))
      .slice(0, 8);
  }, [value, salesReps]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={containerRef} className="relative">
      <input
        type="text"
        placeholder="Buscar vendedor por nombre, email o teléfono..."
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        className="w-full rounded-md border px-3 py-2 text-sm"
      />

      {isOpen && value.trim() !== "" && (
        <div className="absolute z-[1000] mt-1 max-h-64 w-full overflow-y-auto rounded-md border bg-white shadow-md">
          {suggestions.length === 0 ? (
            <p className="px-3 py-2 text-sm text-muted-foreground">
              Sin coincidencias todavía (puede que sigan cargando resultados
              del servidor)
            </p>
          ) : (
            suggestions.map((rep) => (
              <button
                key={rep.id}
                type="button"
                onClick={() => {
                  onSelect(rep.id);
                  setIsOpen(false);
                }}
                className="flex w-full flex-col items-start px-3 py-2 text-left text-sm hover:bg-muted"
              >
                <span className="font-medium">{rep.name}</span>
                {rep.home_lat == null || rep.home_lng == null ? (
                  <span className="text-xs italic text-muted-foreground">
                    Sin coordenadas
                  </span>
                ) : (
                  <span className="text-xs text-muted-foreground">
                    {rep.home_lat.toFixed(4)}, {rep.home_lng.toFixed(4)}
                  </span>
                )}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
