"use client";

import { useState } from "react";
import { Power, RotateCcw, Trash2 } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  useDeletePlatformAdmin,
  usePlatformAdmins,
  useUpdatePlatformAdmin,
} from "@/features/platform/hooks/use-platform-admins";
import { usePlatformAuthStore } from "@/features/platform/store/platform-auth-store";
import type { PlatformAdmin } from "@/features/platform/types";

export function PlatformAdminsList() {
  const currentAdminId = usePlatformAuthStore((state) => state.admin?.id);
  const { data, isLoading, isError, error } = usePlatformAdmins();
  const updateAdmin = useUpdatePlatformAdmin();
  const deleteAdmin = useDeletePlatformAdmin();
  const [deleting, setDeleting] = useState<PlatformAdmin | null>(null);

  const admins = data ?? [];

  if (isLoading) return <p className="text-sm text-muted-foreground">Cargando administradores...</p>;
  if (isError) {
    return (
      <p className="text-sm text-destructive">
        {error instanceof Error ? error.message : "No pudimos cargar los administradores"}
      </p>
    );
  }

  return (
    <>
      <div className="overflow-hidden rounded-3xl bg-card ring-[1.5px] ring-border">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="min-w-[180px]">Nombre</TableHead>
                <TableHead className="min-w-[220px]">Email</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {admins.map((admin) => {
                const isSelf = admin.id === currentAdminId;
                const isToggling =
                  updateAdmin.isPending && updateAdmin.variables?.adminId === admin.id;

                return (
                  <TableRow key={admin.id}>
                    <TableCell className="font-semibold">
                      {admin.name}
                      {isSelf && <span className="ml-2 text-xs font-normal text-muted-foreground">(vos)</span>}
                    </TableCell>
                    <TableCell className="text-muted-foreground">{admin.email}</TableCell>
                    <TableCell>
                      <Badge variant={admin.is_active ? "default" : "secondary"}>
                        {admin.is_active ? "Activo" : "Inactivo"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex justify-end gap-2">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          disabled={isSelf || isToggling}
                          title={isSelf ? "No podés desactivarte a vos mismo" : undefined}
                          onClick={() =>
                            updateAdmin.mutate({ adminId: admin.id, data: { is_active: !admin.is_active } })
                          }
                        >
                          {admin.is_active ? (
                            <Power className="mr-2 h-4 w-4" />
                          ) : (
                            <RotateCcw className="mr-2 h-4 w-4" />
                          )}
                          {admin.is_active ? "Desactivar" : "Activar"}
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          size="icon"
                          disabled={isSelf}
                          aria-label={`Eliminar ${admin.name}`}
                          title={isSelf ? "No podés eliminarte a vos mismo" : undefined}
                          className="border-destructive/20 text-destructive hover:bg-destructive/10 hover:text-destructive"
                          onClick={() => setDeleting(admin)}
                        >
                          <Trash2 className="h-4 w-4" />
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

      <AlertDialog open={!!deleting} onOpenChange={(open) => !open && setDeleting(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Eliminar administrador?</AlertDialogTitle>
            <AlertDialogDescription>
              <strong>{deleting?.name}</strong> ya no va a poder ingresar a la plataforma.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive hover:bg-destructive/90"
              onClick={() => deleting && deleteAdmin.mutate(deleting.id)}
            >
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
