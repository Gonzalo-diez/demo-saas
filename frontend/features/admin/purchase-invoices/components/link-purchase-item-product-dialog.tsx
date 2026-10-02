"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { useProducts } from "@/features/admin/products/hooks/use-products";
import { useLinkPurchaseInvoiceItemProduct } from "@/features/admin/purchase-invoices/hooks/use-link-purchase-invoice-item-product";
import type { PurchaseInvoiceItem } from "@/features/admin/purchase-invoices/types";

type LinkPurchaseItemProductDialogProps = {
  purchaseInvoiceId: number;
  item: PurchaseInvoiceItem;
};

export function LinkPurchaseItemProductDialog({
  purchaseInvoiceId,
  item,
}: LinkPurchaseItemProductDialogProps) {
  const [open, setOpen] = useState(false);
  const [productId, setProductId] = useState<number | null>(item.product_id ?? null);

  const productsQuery = useProducts({
    page: 1,
    page_size: 20,
    search: "",
    status: "active",
    brand: "",
    sort: "name-asc",
  });

  const linkMutation = useLinkPurchaseInvoiceItemProduct();

  const products = productsQuery.data?.items ?? [];

  const suggestedProduct = useMemo(() => {
    const normalizedName = item.product_name.trim().toLowerCase();
    const normalizedSku = item.product_sku?.trim().toLowerCase() ?? null;

    return (
      products.find((product) => {
        const matchesSku =
          normalizedSku &&
          product.sku &&
          product.sku.trim().toLowerCase() === normalizedSku;

        const matchesName =
          product.name.trim().toLowerCase() === normalizedName;

        return matchesSku || matchesName;
      }) ?? null
    );
  }, [item.product_name, item.product_sku, products]);

  async function handleSubmit() {
    try {
      if (!productId) {
        toast.error("Seleccioná un producto", {
          position: "top-right",
          duration: 4000,
        });
        return;
      }

      await linkMutation.mutateAsync({
        purchaseInvoiceId,
        itemId: item.id,
        productId,
      });

      toast.success("Ítem vinculado correctamente", {
        position: "top-right",
        duration: 4000,
      });

      setOpen(false);
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "No se pudo vincular el ítem",
        {
          position: "top-right",
          duration: 4000,
        }
      );
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button type="button" variant="outline" size="sm">
          Vincular producto
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Vincular ítem a producto</DialogTitle>
          <DialogDescription>
            Asociá el ítem importado con un producto existente del catálogo.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="rounded-xl border p-4 text-sm">
            <p>
              <span className="font-medium">Producto detectado:</span>{" "}
              {item.product_name}
            </p>
            <p className="text-muted-foreground">
              SKU: {item.product_sku ?? "-"} · Cantidad: {item.quantity}
            </p>
          </div>

          {suggestedProduct && (
            <div className="rounded-xl border border-chart-3/20 bg-chart-3/10 p-3 text-sm text-chart-3">
              Sugerencia encontrada: <strong>{suggestedProduct.name}</strong>
            </div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-medium">Producto del catálogo</label>
            <Select
              value={productId ? String(productId) : "__empty__"}
              onValueChange={(value) =>
                setProductId(value === "__empty__" ? null : Number(value))
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Seleccionar producto" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__empty__">Seleccionar</SelectItem>
                {products.map((product) => (
                  <SelectItem key={product.id} value={String(product.id)}>
                    {product.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={linkMutation.isPending || productsQuery.isLoading}
          >
            {linkMutation.isPending ? "Guardando..." : "Vincular"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}