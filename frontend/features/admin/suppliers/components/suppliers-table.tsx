"use client";

import { useMemo, useState, Fragment } from "react";
import { Pencil, Power, RotateCcw } from "lucide-react";

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
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import type { Supplier } from "@/features/admin/suppliers/types";
import { useToggleSupplierStatus } from "@/features/admin/suppliers/hooks/use-toggle-supplier-status";
import { EditSupplierDialog } from "@/features/admin/suppliers/components/edit-supplier-dialog";
import { SupplierStatusBadge } from "@/features/admin/suppliers/components/supplier-status-badge";
import { SupplierAccountHistoryDialog } from "@/features/admin/account-movements/components/supplier-account-history-dialog";

type SuppliersTableProps = {
  suppliers: Supplier[];
};

export function SuppliersTable({ suppliers }: SuppliersTableProps) {
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null);
  const toggleStatus = useToggleSupplierStatus();

  const empty = useMemo(() => suppliers.length === 0, [suppliers]);

  return (
    <Fragment>
      <div className="space-y-4">
        {empty ? (
          <div className="rounded-2xl border bg-background px-4 py-10 text-center text-sm text-muted-foreground shadow-sm">
            No hay proveedores para mostrar.
          </div>
        ) : (
          <div className="space-y-3 md:hidden">
            {suppliers.map((supplier) => {
              const isToggling =
                toggleStatus.isPending &&
                toggleStatus.variables?.supplierId === supplier.id;

              return (
                <div key={supplier.id} className="space-y-4 rounded-2xl border bg-background p-4 shadow-sm">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 space-y-1">
                      <p className="truncate font-semibold">{supplier.name}</p>
                      <p className="text-xs text-muted-foreground">CUIT: {supplier.tax_id ?? "-"}</p>
                    </div>
                    <SupplierStatusBadge isActive={supplier.is_active} />
                  </div>

                  <div className="grid gap-3 text-sm sm:grid-cols-2">
                    <div className="rounded-xl border p-3">
                      <p className="text-xs text-muted-foreground">Email</p>
                      <p className="break-words font-medium">{supplier.email ?? "-"}</p>
                    </div>
                    <div className="rounded-xl border p-3">
                      <p className="text-xs text-muted-foreground">Teléfono</p>
                      <p className="font-medium">{supplier.phone ?? "-"}</p>
                    </div>
                    <div className="rounded-xl border p-3 sm:col-span-2">
                      <p className="text-xs text-muted-foreground">Dirección</p>
                      <p className="font-medium">{supplier.address ?? "-"}</p>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2 sm:flex-row">
                    <Button
                      type="button"
                      variant="outline"
                      className="w-full sm:flex-1"
                      onClick={() => setSelectedSupplier(supplier)}
                    >
                      <Pencil className="mr-2 h-4 w-4" />
                      Editar
                    </Button>

                    <div className="w-full sm:flex-1">
                      <SupplierAccountHistoryDialog supplier={supplier} />
                    </div>

                    {supplier.is_active ? (
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button
                            type="button"
                            variant="outline"
                            className="w-full border-destructive/20 text-destructive hover:bg-destructive/10 hover:text-destructive sm:flex-1"
                            disabled={isToggling}
                          >
                            <Power className="mr-2 h-4 w-4" />
                            {isToggling ? "Guardando..." : "Desactivar"}
                          </Button>
                        </AlertDialogTrigger>

                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>¿Desactivar proveedor?</AlertDialogTitle>
                            <AlertDialogDescription>
                              Esta acción desactivará el proveedor <strong>{supplier.name}</strong>.
                              Podrás volver a activarlo más tarde.
                            </AlertDialogDescription>
                          </AlertDialogHeader>

                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancelar</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() =>
                                toggleStatus.mutate({
                                  supplierId: supplier.id,
                                  nextStatus: "inactive",
                                  supplierName: supplier.name,
                                })
                              }
                              className="bg-destructive hover:bg-destructive/90"
                            >
                              Confirmar
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    ) : (
                      <Button
                        type="button"
                        variant="outline"
                        className="w-full border-brand/20 text-brand hover:bg-brand/10 hover:text-brand sm:flex-1"
                        disabled={isToggling}
                        onClick={() =>
                          toggleStatus.mutate({
                            supplierId: supplier.id,
                            nextStatus: "active",
                            supplierName: supplier.name,
                          })
                        }
                      >
                        <RotateCcw className="mr-2 h-4 w-4" />
                        {isToggling ? "Guardando..." : "Activar"}
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {!empty ? (
          <div className="hidden overflow-hidden rounded-2xl border bg-background shadow-sm md:block">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="min-w-[220px]">Nombre</TableHead>
                    <TableHead>CUIT</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Teléfono</TableHead>
                    <TableHead>Dirección</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {suppliers.map((supplier) => {
                    const isToggling =
                      toggleStatus.isPending &&
                      toggleStatus.variables?.supplierId === supplier.id;

                    return (
                      <TableRow key={supplier.id}>
                        <TableCell className="max-w-[220px] truncate font-medium">{supplier.name}</TableCell>
                        <TableCell>{supplier.tax_id ?? "-"}</TableCell>
                        <TableCell>{supplier.email ?? "-"}</TableCell>
                        <TableCell>{supplier.phone ?? "-"}</TableCell>
                        <TableCell className="max-w-[260px] truncate">{supplier.address ?? "-"}</TableCell>
                        <TableCell>
                          <SupplierStatusBadge isActive={supplier.is_active} />
                        </TableCell>
                        <TableCell>
                          <div className="flex justify-end gap-2">
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={() => setSelectedSupplier(supplier)}
                            >
                              <Pencil className="mr-2 h-4 w-4" />
                              Editar
                            </Button>

                            <SupplierAccountHistoryDialog supplier={supplier} />

                            {supplier.is_active ? (
                              <AlertDialog>
                                <AlertDialogTrigger asChild>
                                  <Button
                                    type="button"
                                    variant="outline"
                                    size="sm"
                                    disabled={isToggling}
                                    className="border-destructive/20 text-destructive hover:bg-destructive/10 hover:text-destructive"
                                  >
                                    <Power className="mr-2 h-4 w-4" />
                                    {isToggling ? "Guardando..." : "Desactivar"}
                                  </Button>
                                </AlertDialogTrigger>

                                <AlertDialogContent>
                                  <AlertDialogHeader>
                                    <AlertDialogTitle>¿Desactivar proveedor?</AlertDialogTitle>
                                    <AlertDialogDescription>
                                      Esta acción desactivará el proveedor <strong>{supplier.name}</strong>.
                                      Podrás volver a activarlo más tarde.
                                    </AlertDialogDescription>
                                  </AlertDialogHeader>

                                  <AlertDialogFooter>
                                    <AlertDialogCancel>Cancelar</AlertDialogCancel>
                                    <AlertDialogAction
                                      onClick={() =>
                                        toggleStatus.mutate({
                                          supplierId: supplier.id,
                                          nextStatus: "inactive",
                                          supplierName: supplier.name,
                                        })
                                      }
                                      className="bg-destructive hover:bg-destructive/90"
                                    >
                                      Confirmar
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
                                    supplierId: supplier.id,
                                    nextStatus: "active",
                                    supplierName: supplier.name,
                                  })
                                }
                                className="border-brand/20 text-brand hover:bg-brand/10 hover:text-brand"
                              >
                                <RotateCcw className="mr-2 h-4 w-4" />
                                {isToggling ? "Guardando..." : "Activar"}
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          </div>
        ) : null}
      </div>

      <EditSupplierDialog
        open={!!selectedSupplier}
        supplier={selectedSupplier}
        onClose={() => setSelectedSupplier(null)}
      />
    </Fragment>
  );
}