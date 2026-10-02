"use client";

import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import type { Client, ClientBranch } from "@/features/admin/clients/types";
import { useClientBranches } from "@/features/admin/clients/hooks/use-client-branches";
import { useToggleClientBranchStatus } from "@/features/admin/clients/hooks/use-toggle-client-branch-status";
import { ClientBranchForm } from "@/features/admin/clients/components/client-branch-form";

type Props = {
  client: Client;
};

export function ClientBranchesManager({ client }: Props) {
  const [isCreating, setIsCreating] = useState(false);
  const [editingBranch, setEditingBranch] = useState<ClientBranch | null>(null);

  const branchesQuery = useClientBranches(client.id);
  const toggleBranchStatus = useToggleClientBranchStatus();

  const branches = branchesQuery.data ?? [];

  async function handleToggle(branch: ClientBranch) {
    try {
      await toggleBranchStatus.mutateAsync({
        clientId: client.id,
        branchId: branch.id,
        isActive: branch.is_active,
      });

      toast.success(
        branch.is_active ? "Sucursal desactivada" : "Sucursal activada"
      );
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "No se pudo cambiar el estado"
      );
    }
  }

  return (
    <div className="space-y-4 rounded-2xl border bg-card p-6 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h4 className="text-sm font-semibold">Sucursales</h4>
          <p className="text-xs text-muted-foreground">
            Administrá las ubicaciones operativas del cliente.
          </p>
        </div>

        <Button
          type="button"
          variant="outline"
          onClick={() => {
            setEditingBranch(null);
            setIsCreating((prev) => !prev);
          }}
        >
          {isCreating ? "Cerrar" : "Agregar sucursal"}
        </Button>
      </div>

      {isCreating ? (
        <ClientBranchForm
          clientId={client.id}
          onSuccess={() => setIsCreating(false)}
          onCancel={() => setIsCreating(false)}
        />
      ) : null}

      {editingBranch ? (
        <ClientBranchForm
          clientId={client.id}
          branch={editingBranch}
          onSuccess={() => setEditingBranch(null)}
          onCancel={() => setEditingBranch(null)}
        />
      ) : null}

      {branchesQuery.isLoading ? (
        <p className="text-sm text-muted-foreground">Cargando sucursales...</p>
      ) : branchesQuery.isError ? (
        <p className="text-sm text-destructive">
          Error al cargar sucursales
        </p>
      ) : branches.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Este cliente no tiene sucursales todavía.
        </p>
      ) : (
        <div className="space-y-3">
          {branches.map((branch) => (
            <div
              key={branch.id}
              className="rounded-xl border p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <p className="font-medium">
                    {branch.name}
                    {branch.is_main ? " (Principal)" : ""}
                  </p>
                  {branch.address ? (
                    <p className="text-sm text-muted-foreground">{branch.address}</p>
                  ) : null}
                  {branch.city ? (
                    <p className="text-sm text-muted-foreground">{branch.city}</p>
                  ) : null}
                  <p className="text-xs text-muted-foreground">
                    Estado: {branch.is_active ? "Activa" : "Inactiva"}
                  </p>
                </div>

                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setIsCreating(false);
                      setEditingBranch(branch);
                    }}
                  >
                    Editar
                  </Button>

                  {!branch.is_main ? (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => handleToggle(branch)}
                    >
                      {branch.is_active ? "Desactivar" : "Activar"}
                    </Button>
                  ) : null}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}