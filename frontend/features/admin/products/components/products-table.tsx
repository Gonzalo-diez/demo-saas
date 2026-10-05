"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { History, Pencil, Power, RotateCcw } from "lucide-react";
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
import type { Product, ProductStatusFilter } from "@/features/admin/products/types";
import { useToggleProductStatus } from "@/features/admin/products/hooks/use-toggle-product-status";
import { EditProductDialog } from "@/features/admin/products/components/edit-product-dialog";
import { ProductActiveBadge } from "@/features/admin/products/components/product-active-badge";
import { ProductVisibilityBadge } from "@/features/admin/products/components/product-visibility-badge";
import { ProductVisibilityButton } from "@/features/admin/products/components/product-visibility-button";
import { ProductStatusBadge } from "@/features/admin/products/components/product-status-badge";

type ProductsTableProps = {
  products: Product[];
};

function formatCurrency(value: number | string) {
  const numericValue = Number(value);

  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 2,
  }).format(Number.isNaN(numericValue) ? 0 : numericValue);
}

export function ProductsTable({ products }: ProductsTableProps) {
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const toggleStatus = useToggleProductStatus();

  const empty = useMemo(() => products.length === 0, [products]);

  return (
    <>
      <div className="space-y-4">
        {empty ? (
          <div className="rounded-2xl border bg-background px-4 py-10 text-center text-sm text-muted-foreground shadow-sm">
            No hay productos para mostrar.
          </div>
        ) : (
          <div className="space-y-3 md:hidden">
            {products.map((product) => {
              const isToggling =
                toggleStatus.isPending &&
                toggleStatus.variables?.productId === product.id;

              const unitCost = Number(product.unit_cost);
              const unitPrice = Number(product.unit_price);
              const unitMargin = unitPrice - unitCost;

              return (
                <div
                  key={product.id}
                  className="space-y-4 rounded-2xl border bg-background p-4 shadow-sm"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 space-y-1">
                      <p className="truncate font-semibold">{product.name}</p>
                      <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                        <span>{product.brand ?? "Sin marca"}</span>
                        <span>•</span>
                        <span>{product.category ?? "Sin categoría"}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        SKU: {product.sku || "-"}
                      </p>
                    </div>

                    <div className="flex flex-col items-end gap-1.5">
                      <ProductActiveBadge isActive={product.is_active} />
                      <ProductVisibilityBadge isPublic={product.is_public} />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="rounded-xl border p-3">
                      <p className="text-xs text-muted-foreground">Costo</p>
                      <p className="font-medium">{formatCurrency(unitCost)}</p>
                    </div>
                    <div className="rounded-xl border p-3">
                      <p className="text-xs text-muted-foreground">Venta</p>
                      <p className="font-medium">{formatCurrency(unitPrice)}</p>
                    </div>
                    <div className="rounded-xl border p-3">
                      <p className="text-xs text-muted-foreground">Margen</p>
                      <p className="font-medium">{formatCurrency(unitMargin)}</p>
                    </div>
                    <div className="rounded-xl border p-3">
                      <p className="text-xs text-muted-foreground">Stock</p>
                      <p className="font-medium">
                        {product.stock_current} / mín. {product.stock_min}
                      </p>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2 sm:flex-row">
                    <Button
                      type="button"
                      variant="outline"
                      className="w-full sm:flex-1"
                      onClick={() => setSelectedProduct(product)}
                    >
                      <Pencil className="mr-2 h-4 w-4" />
                      Editar
                    </Button>

                    <Button asChild variant="outline" className="w-full sm:flex-1">
                      <Link href={`/admin/products/${product.id}/purchases`}>
                        <History className="mr-2 h-4 w-4" />
                        Compras
                      </Link>
                    </Button>

                    <ProductVisibilityButton
                      product={product}
                      size="default"
                      className="w-full sm:flex-1"
                    />

                    {product.is_active ? (
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
                            <AlertDialogTitle>¿Desactivar producto?</AlertDialogTitle>
                            <AlertDialogDescription>
                              Esta acción desactivará el producto <strong>{product.name}</strong>.
                              Podrás volver a activarlo más tarde.
                            </AlertDialogDescription>
                          </AlertDialogHeader>

                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancelar</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() =>
                                toggleStatus.mutate({
                                  productId: product.id,
                                  nextStatus: "inactive",
                                  productName: product.name,
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
                            productId: product.id,
                            nextStatus: "active",
                            productName: product.name,
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
                    <TableHead>Marca</TableHead>
                    <TableHead>Categoría</TableHead>
                    <TableHead>SKU</TableHead>
                    <TableHead className="text-right">Costo</TableHead>
                    <TableHead className="text-right">Venta</TableHead>
                    <TableHead className="text-right">Margen</TableHead>
                    <TableHead className="text-right">Stock actual</TableHead>
                    <TableHead className="text-right">Stock mínimo</TableHead>
                    <TableHead>Activo/Inactivo</TableHead>
                    <TableHead>Catálogo</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {products.map((product) => {
                    const isToggling =
                      toggleStatus.isPending &&
                      toggleStatus.variables?.productId === product.id;

                    const unitCost = Number(product.unit_cost);
                    const unitPrice = Number(product.unit_price);
                    const unitMargin = unitPrice - unitCost;

                    return (
                      <TableRow key={product.id}>
                        <TableCell className="max-w-[220px] truncate font-medium">
                          {product.name}
                        </TableCell>
                        <TableCell>{product.brand ?? "-"}</TableCell>
                        <TableCell>{product.category ?? "-"}</TableCell>
                        <TableCell>{product.sku}</TableCell>
                        <TableCell className="text-right">{formatCurrency(unitCost)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(unitPrice)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(unitMargin)}</TableCell>
                        <TableCell className="text-right">{product.stock_current}</TableCell>
                        <TableCell className="text-right">{product.stock_min}</TableCell>
                        <TableCell>
                          <ProductActiveBadge isActive={product.is_active} />
                        </TableCell>
                        <TableCell>
                          <ProductVisibilityBadge isPublic={product.is_public} />
                        </TableCell>
                        <TableCell>
                          <ProductStatusBadge
                            status={
                              product.status.toLowerCase() as ProductStatusFilter
                            }
                          />
                        </TableCell>
                        <TableCell>
                          <div className="flex justify-end gap-2">
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={() => setSelectedProduct(product)}
                            >
                              <Pencil className="mr-2 h-4 w-4" />
                              Editar
                            </Button>

                            <Button asChild type="button" variant="outline" size="sm">
                              <Link href={`/admin/products/${product.id}/purchases`}>
                                <History className="mr-2 h-4 w-4" />
                                Compras
                              </Link>
                            </Button>

                            <ProductVisibilityButton product={product} />

                            {product.is_active ? (
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
                                    <AlertDialogTitle>¿Desactivar producto?</AlertDialogTitle>
                                    <AlertDialogDescription>
                                      Esta acción desactivará el producto <strong>{product.name}</strong>.
                                      Podrás volver a activarlo más tarde.
                                    </AlertDialogDescription>
                                  </AlertDialogHeader>

                                  <AlertDialogFooter>
                                    <AlertDialogCancel>Cancelar</AlertDialogCancel>
                                    <AlertDialogAction
                                      onClick={() =>
                                        toggleStatus.mutate({
                                          productId: product.id,
                                          nextStatus: "inactive",
                                          productName: product.name,
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
                                    productId: product.id,
                                    nextStatus: "active",
                                    productName: product.name,
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

      <EditProductDialog
        open={!!selectedProduct}
        product={selectedProduct}
        onClose={() => setSelectedProduct(null)}
      />
    </>
  );
}