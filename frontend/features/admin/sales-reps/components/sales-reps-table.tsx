"use client";

import { useState, Fragment } from "react";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import type { SalesRep } from "@/features/admin/sales-reps/types";
import { SalesRepStatusBadge } from "@/features/admin/sales-reps/components/sales-rep-status-badge";
import { EditSalesRepDialog } from "@/features/admin/sales-reps/components/edit-sales-rep-dialog";
import { useToggleSalesRepStatus } from "@/features/admin/sales-reps/hooks/use-toggle-sales-rep-status";
import { useAuthStore } from "@/features/admin/auth/store/auth-store";

type SalesRepsTableProps = {
  salesReps: SalesRep[];
};

export function SalesRepsTable({ salesReps }: SalesRepsTableProps) {
  const [selectedSalesRep, setSelectedSalesRep] = useState<SalesRep | null>(
    null,
  );
  const toggleStatus = useToggleSalesRepStatus();
  const isSuperuser = useAuthStore(
    (state) => state.user?.is_superuser ?? false,
  );

  return (
    <Fragment>
      <div className="overflow-hidden rounded-xl border bg-background shadow-sm">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nombre</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Teléfono</TableHead>
                <TableHead>Rol</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Latitud</TableHead>
                <TableHead>Longitud</TableHead>
                <TableHead>Km de covertura</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {salesReps.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={10}
                    className="py-8 text-center text-sm text-muted-foreground"
                  >
                    No hay vendedores para mostrar.
                  </TableCell>
                </TableRow>
              ) : (
                salesReps.map((salesRep) => {
                  const isToggling =
                    toggleStatus.isPending &&
                    toggleStatus.variables?.salesRepId === salesRep.id;

                  return (
                    <TableRow key={salesRep.id}>
                      <TableCell className="font-medium">
                        {salesRep.name}
                      </TableCell>
                      <TableCell>{salesRep.email}</TableCell>
                      <TableCell>{salesRep.phone ?? "-"}</TableCell>
                      <TableCell>
                        {salesRep.is_superuser ? "Superusuario" : "Vendedor"}
                      </TableCell>
                      <TableCell>
                        <SalesRepStatusBadge isActive={salesRep.is_active} />
                      </TableCell>
                      <TableCell>{salesRep.home_lat ?? "-"}</TableCell>
                      <TableCell>{salesRep.home_lng ?? "-"}</TableCell>
                      <TableCell>
                        {salesRep.coverage_radius_km ?? "-"}
                      </TableCell>
                      <TableCell>
                        {isSuperuser ? (
                          <div className="flex justify-end gap-2">
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={() => setSelectedSalesRep(salesRep)}
                            >
                              Editar
                            </Button>

                            {salesRep.is_active ? (
                              <AlertDialog>
                                <AlertDialogTrigger asChild>
                                  <Button
                                    type="button"
                                    variant="outline"
                                    size="sm"
                                    disabled={isToggling}
                                    className="border-destructive/20 text-destructive hover:bg-destructive/10 hover:text-destructive"
                                  >
                                    {isToggling ? "Guardando..." : "Desactivar"}
                                  </Button>
                                </AlertDialogTrigger>

                                <AlertDialogContent>
                                  <AlertDialogHeader>
                                    <AlertDialogTitle>
                                      ¿Desactivar vendedor?
                                    </AlertDialogTitle>
                                    <AlertDialogDescription>
                                      Esta acción desactivará a{" "}
                                      <strong>{salesRep.name}</strong>.
                                    </AlertDialogDescription>
                                  </AlertDialogHeader>

                                  <AlertDialogFooter>
                                    <AlertDialogCancel>
                                      Cancelar
                                    </AlertDialogCancel>
                                    <AlertDialogAction
                                      onClick={() =>
                                        toggleStatus.mutate({
                                          salesRepId: salesRep.id,
                                          nextStatus: "inactive",
                                          salesRepName: salesRep.name,
                                        })
                                      }
                                    >
                                      Desactivar
                                    </AlertDialogAction>
                                  </AlertDialogFooter>
                                </AlertDialogContent>
                              </AlertDialog>
                            ) : (
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                disabled={isToggling}
                                onClick={() =>
                                  toggleStatus.mutate({
                                    salesRepId: salesRep.id,
                                    nextStatus: "active",
                                    salesRepName: salesRep.name,
                                  })
                                }
                                className="border-brand/20 text-brand hover:bg-brand/10 hover:text-brand"
                              >
                                {isToggling ? "Guardando..." : "Activar"}
                              </Button>
                            )}
                          </div>
                        ) : (
                          <div className="flex justify-end">
                            <span className="text-sm text-muted-foreground">
                              -
                            </span>
                          </div>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      {isSuperuser && (
        <EditSalesRepDialog
          open={!!selectedSalesRep}
          salesRep={selectedSalesRep}
          onClose={() => setSelectedSalesRep(null)}
        />
      )}
    </Fragment>
  );
}