"use client";

import { Power, PowerOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Client } from "@/features/admin/clients/types";
import { EditClientDialog } from "@/features/admin/clients/components/edit-client-dialog";
import { useToggleClientStatus } from "@/features/admin/clients/hooks/use-toggle-client-status";
import { EditClientBranchesDialog } from "@/features/admin/clients/components/edit-client-branch-dialog";
import { ClientAccountHistoryDialog } from "@/features/admin/account-movements/components/client-account-history-dialog";

type ClientsTableProps = {
  clients: Client[];
};

function ClientStatusPill({ isActive }: { isActive: boolean }) {
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${isActive
          ? "bg-brand-muted text-brand"
          : "bg-destructive/15 text-destructive"
        }`}
    >
      {isActive ? "Activo" : "Inactivo"}
    </span>
  );
}

export function ClientsTable({ clients }: ClientsTableProps) {
  const toggleClientStatus = useToggleClientStatus();

  async function handleToggleStatus(client: Client) {
    await toggleClientStatus.mutateAsync({
      clientId: client.id,
      clientName: client.name,
      isActive: client.is_active,
    });
  }

  if (clients.length === 0) {
    return (
      <div className="rounded-2xl border bg-background px-4 py-8 text-center text-sm text-muted-foreground shadow-sm">
        No hay clientes para mostrar.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="space-y-3 md:hidden">
        {clients.map((client) => {
          const mainBranch = client.branches.find((branch) => branch.is_main) ?? null;
          const isToggling =
            toggleClientStatus.isPending &&
            toggleClientStatus.variables?.clientId === client.id;

          return (
            <div key={client.id} className="space-y-4 rounded-2xl border bg-background p-4 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 space-y-1">
                  <p className="truncate font-semibold">{client.name}</p>
                  <p className="text-xs text-muted-foreground">ID #{client.id}</p>
                  <p className="text-xs text-muted-foreground">{client.client_type || "-"}</p>
                </div>
                <ClientStatusPill isActive={client.is_active} />
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-xl border p-3">
                  <p className="text-xs text-muted-foreground">CUIT</p>
                  <p className="font-medium">{client.tax_id ?? "-"}</p>
                </div>
                <div className="rounded-xl border p-3">
                  <p className="text-xs text-muted-foreground">Sucursales</p>
                  <p className="font-medium">{client.branches.length}</p>
                </div>
              </div>

              <div className="rounded-xl border p-3 text-sm">
                <p className="mb-1 text-xs text-muted-foreground">Sucursal principal</p>
                {mainBranch ? (
                  <div className="space-y-1">
                    <p className="font-medium">{mainBranch.name}</p>
                    {mainBranch.city ? <p className="text-muted-foreground">{mainBranch.city}</p> : null}
                    {mainBranch.address ? <p className="text-muted-foreground">{mainBranch.address}</p> : null}
                  </div>
                ) : (
                  <p className="text-muted-foreground">-</p>
                )}
              </div>

              <div className="flex flex-col gap-2 sm:flex-row">
                <div className="w-full sm:flex-1">
                  <EditClientDialog client={client} />
                </div>

                <div className="w-full sm:flex-1">
                  <EditClientBranchesDialog client={client} />
                </div>

                <div className="w-full sm:flex-1">
                  <ClientAccountHistoryDialog client={client} />
                </div>

                <Button
                  type="button"
                  variant="outline"
                  className="w-full sm:flex-1"
                  onClick={() => handleToggleStatus(client)}
                  disabled={isToggling}
                >
                  {client.is_active ? (
                    <>
                      <PowerOff className="mr-2 h-4 w-4" />
                      {isToggling ? "Guardando..." : "Desactivar"}
                    </>
                  ) : (
                    <>
                      <Power className="mr-2 h-4 w-4" />
                      {isToggling ? "Guardando..." : "Activar"}
                    </>
                  )}
                </Button>
              </div>
            </div>
          );
        })}
      </div>

      <div className="hidden overflow-hidden rounded-2xl border bg-background shadow-sm md:block">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Cliente</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>CUIT</TableHead>
                <TableHead>Sucursales</TableHead>
                <TableHead>Sucursal principal</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {clients.map((client) => {
                const mainBranch = client.branches.find((branch) => branch.is_main) ?? null;
                const isToggling =
                  toggleClientStatus.isPending &&
                  toggleClientStatus.variables?.clientId === client.id;

                return (
                  <TableRow key={client.id}>
                    <TableCell>
                      <div className="space-y-1">
                        <p className="font-medium">{client.name}</p>
                        <p className="text-xs text-muted-foreground">ID #{client.id}</p>
                      </div>
                    </TableCell>
                    <TableCell className="capitalize">{client.client_type || "-"}</TableCell>
                    <TableCell>{client.tax_id ?? "-"}</TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <p className="font-medium">{client.branches.length}</p>
                        <p className="text-xs text-muted-foreground">
                          {client.branches.length === 1 ? "sucursal registrada" : "sucursales registradas"}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell>
                      {mainBranch ? (
                        <div className="space-y-1">
                          <p className="font-medium">{mainBranch.name}</p>
                          {mainBranch.city ? <p className="text-xs text-muted-foreground">{mainBranch.city}</p> : null}
                          {mainBranch.address ? <p className="text-xs text-muted-foreground">{mainBranch.address}</p> : null}
                        </div>
                      ) : (
                        <span className="text-sm text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <ClientStatusPill isActive={client.is_active} />
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <EditClientDialog client={client} />

                        <EditClientBranchesDialog client={client} />

                        <ClientAccountHistoryDialog client={client} />

                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => handleToggleStatus(client)}
                          disabled={isToggling}
                        >
                          {client.is_active ? (
                            <>
                              <PowerOff className="mr-2 h-4 w-4" />
                              {isToggling ? "Guardando..." : "Desactivar"}
                            </>
                          ) : (
                            <>
                              <Power className="mr-2 h-4 w-4" />
                              {isToggling ? "Guardando..." : "Activar"}
                            </>
                          )}
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}