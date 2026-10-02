"use client";

import type { MapClient } from "@/features/admin/client-map/types";

type MapSidebarProps = {
  clients: MapClient[];
  isLoading: boolean;
  isError: boolean;
  selectedBranchId: number | null;
  onSelectBranch: (branchId: number) => void;
};

export function MapSidebar({
  clients,
  isLoading,
  isError,
  selectedBranchId,
  onSelectBranch,
}: MapSidebarProps) {
  if (isLoading) {
    return (
      <div className="h-[600px] rounded-xl border p-4">
        Cargando sucursales...
      </div>
    );
  }

  if (isError) {
    return (
      <div className="h-[600px] rounded-xl border p-4">
        Error al cargar sucursales
      </div>
    );
  }

  if (clients.length === 0) {
    return (
      <div className="h-[600px] rounded-xl border p-4">
        No hay sucursales para mostrar
      </div>
    );
  }

  return (
    <div className="h-[600px] overflow-y-auto rounded-xl border p-2">
      <div className="space-y-2">
        {clients.map((client) => {
          const isSelected = selectedBranchId === client.branch_id;

          return (
            <button
              key={client.branch_id}
              type="button"
              onClick={() => onSelectBranch(client.branch_id)}
              className={`w-full rounded-lg border p-3 text-left transition ${
                isSelected ? "border-primary bg-muted" : "hover:bg-muted/50"
              }`}
            >
              <p className="font-medium">{client.client_name}</p>

              <p className="text-sm">
                {client.branch_name}
                {client.branch_is_main ? " (Principal)" : ""}
              </p>

              {client.branch_address ? (
                <p className="text-sm text-muted-foreground">
                  {client.branch_address}
                </p>
              ) : null}

              {client.branch_city ? (
                <p className="text-sm text-muted-foreground">
                  {client.branch_city}
                </p>
              ) : null}

              {client.sales_rep_name ? (
                <p className="text-xs text-muted-foreground">
                  Vendedor: {client.sales_rep_name}
                </p>
              ) : null}
            </button>
          );
        })}
      </div>
    </div>
  );
}