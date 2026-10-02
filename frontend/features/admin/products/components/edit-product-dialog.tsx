"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { CreateProductForm } from "@/features/admin/products/components/create-product-form";
import type { Product } from "@/features/admin/products/types";

type EditProductDialogProps = {
  open: boolean;
  product: Product | null;
  onClose: () => void;
};

export function EditProductDialog({
  open,
  product,
  onClose,
}: EditProductDialogProps) {
  if (!product) return null;

  return (
    <Dialog open={open} onOpenChange={(value) => !value && onClose()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto px-4 sm:max-w-3xl sm:px-6">
        <DialogHeader>
          <DialogTitle>Editar producto</DialogTitle>
          <DialogDescription>
            Modificá los datos del producto y guardá los cambios.
          </DialogDescription>
        </DialogHeader>

        <div className="rounded-2xl border bg-card p-4 shadow-sm sm:p-6">
          <CreateProductForm
            mode="edit"
            initialData={product}
            onSuccess={onClose}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
}