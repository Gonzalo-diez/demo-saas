"use client";

import { useState } from "react";
import { Eye, EyeOff, Pencil, Trash2 } from "lucide-react";
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
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { CategoryFormDialog } from "@/features/admin/categories/components/category-form-dialog";
import { useCategories } from "@/features/admin/categories/hooks/use-categories";
import {
  useDeleteCategory,
  useSetCategoryPublic,
} from "@/features/admin/categories/hooks/use-category-mutations";
import type { Category } from "@/features/admin/categories/types";

export function CategoriesList() {
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<Category | null>(null);
  const [deleting, setDeleting] = useState<Category | null>(null);

  const { data, isLoading, isError, error } = useCategories({
    search: search.trim() || undefined,
  });
  const setPublic = useSetCategoryPublic();
  const deleteCategory = useDeleteCategory();

  const categories = data?.items ?? [];

  return (
    <div className="space-y-4">
      <Input
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        placeholder="Buscar categoría..."
        className="max-w-sm"
      />

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Cargando categorías...</p>
      ) : isError ? (
        <p className="text-sm text-destructive">
          {error instanceof Error ? error.message : "No pudimos cargar las categorías"}
        </p>
      ) : categories.length === 0 ? (
        <div className="rounded-3xl border border-dashed bg-card px-4 py-12 text-center">
          <h3 className="text-lg font-semibold">
            {search ? "No hay categorías con ese nombre" : "Todavía no creaste categorías"}
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">
            {search
              ? "Probá con otra búsqueda."
              : "Creá la primera para poder asignarla a tus productos y armar tu catálogo."}
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-3xl bg-card ring-[1.5px] ring-border">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="min-w-[200px]">Nombre</TableHead>
                  <TableHead className="min-w-[220px]">Descripción</TableHead>
                  <TableHead className="text-right">Productos</TableHead>
                  <TableHead>Catálogo</TableHead>
                  <TableHead>Edad</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {categories.map((category) => {
                  const isToggling =
                    setPublic.isPending &&
                    setPublic.variables?.categoryId === category.id;

                  return (
                    <TableRow key={category.id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          {category.image_url ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img
                              src={category.image_url}
                              alt={category.name}
                              className="h-10 w-10 shrink-0 rounded-lg border object-contain"
                            />
                          ) : (
                            <div
                              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-dashed bg-muted/40 text-[10px] text-muted-foreground"
                              title="Sin imagen"
                            >
                              Sin img
                            </div>
                          )}
                          <div className="min-w-0">
                            <p className="font-semibold">{category.name}</p>
                            <p className="text-xs text-muted-foreground">/{category.slug}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="max-w-[320px] truncate text-muted-foreground">
                        {category.description ?? "-"}
                      </TableCell>
                      <TableCell className="text-right">{category.product_count}</TableCell>
                      <TableCell>
                        <Badge variant={category.is_public ? "default" : "secondary"}>
                          {category.is_public ? "Pública" : "Privada"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {category.requires_age_verification ? (
                          <Badge className="bg-stamp text-stamp-foreground">+18</Badge>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex justify-end gap-2">
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => setEditing(category)}
                          >
                            <Pencil className="mr-2 h-4 w-4" />
                            Editar
                          </Button>

                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            disabled={isToggling}
                            onClick={() =>
                              setPublic.mutate({
                                categoryId: category.id,
                                isPublic: !category.is_public,
                              })
                            }
                          >
                            {category.is_public ? (
                              <EyeOff className="mr-2 h-4 w-4" />
                            ) : (
                              <Eye className="mr-2 h-4 w-4" />
                            )}
                            {category.is_public ? "Ocultar" : "Publicar"}
                          </Button>

                          <Button
                            type="button"
                            variant="outline"
                            size="icon"
                            aria-label={`Eliminar ${category.name}`}
                            className="border-destructive/20 text-destructive hover:bg-destructive/10 hover:text-destructive"
                            onClick={() => setDeleting(category)}
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
      )}

      <CategoryFormDialog
        key={editing?.id ?? "none"}
        category={editing}
        open={!!editing}
        onOpenChange={(open) => {
          if (!open) setEditing(null);
        }}
      />

      <AlertDialog
        open={!!deleting}
        onOpenChange={(open) => {
          if (!open) setDeleting(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Eliminar categoría?</AlertDialogTitle>
            <AlertDialogDescription>
              Vas a eliminar <strong>{deleting?.name}</strong>. Si tiene productos no se
              puede borrar: movelos a otra categoría o ocultala del catálogo.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive hover:bg-destructive/90"
              onClick={() => deleting && deleteCategory.mutate(deleting.id)}
            >
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
