"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { CreateSupplierForm } from "@/features/admin/suppliers/components/create-supplier-form";
import type { Supplier } from "@/features/admin/suppliers/types";

type EditSupplierDialogProps = {
  open: boolean;
  supplier: Supplier | null;
  onClose: () => void;
};

export function EditSupplierDialog({
  open,
  supplier,
  onClose,
}: EditSupplierDialogProps) {
  if (!supplier) return null;

  return (
    <Dialog open={open} onOpenChange={(value) => !value && onClose()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto px-4 sm:max-w-2xl sm:px-6">
        <DialogHeader>
          <DialogTitle>Editar proveedor</DialogTitle>
          <DialogDescription>
            Modificá los datos del proveedor y guardá los cambios.
          </DialogDescription>
        </DialogHeader>

        <div className="rounded-2xl border bg-card p-4 shadow-sm sm:p-6">
          <CreateSupplierForm
            mode="edit"
            initialData={supplier}
            onSuccess={onClose}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
}